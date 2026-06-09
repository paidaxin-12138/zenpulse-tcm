// Copyright (c) 2026 paidaxin-12138
// Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
// https://creativecommons.org/licenses/by-nc/4.0/

// metrics.js
import { analyzeVitals, bootstrapServer, getHealthMetrics } from '../../utils/api';
import { captureBleVitals, BLE_DEFAULT_FS } from '../../utils/bleVitals';
import {
  ensurePrivacyAuthorized,
  getPrivacySetting,
  isPrivacyApiBannedError,
  openPrivacyContract,
  privacyBannedMessage
} from '../../utils/privacy';
import { downsampleForPreview } from '../../utils/pulseCapture';
import { getAppSafe } from '../../utils/appContext';

Page({
  data: {
    metrics: {
      heart_rate: '',
      pulse: '',
      systolic: '',
      diastolic: '',
      age: '',
      gender: '',
      pulse_waveform: [],
      max30102_samples_ch2: [],
      pulse_fs: BLE_DEFAULT_FS,
      pulse_source: 'manual',
      spo2: '',
      vitals_assessment: null
    },
    vitalsCapture: {
      active: false,
      progress: 0,
      statusText: '',
      done: false,
      heartRate: '',
      spo2: '',
      hrStatus: '',
      spo2Status: '',
      overallStatus: '',
      sampleCount: 0,
      previewPoints: [],
      alerts: [],
      limitations: []
    },
    privacyNeedAuth: false,
    privacyContractName: '用户隐私保护指引'
  },

  refreshPrivacySetting() {
    return getPrivacySetting().then(({ needAuthorization, privacyContractName }) => {
      this.setData({
        privacyNeedAuth: needAuthorization,
        privacyContractName: privacyContractName || '用户隐私保护指引'
      });
    });
  },

  onOpenPrivacyContract() {
    openPrivacyContract();
  },

  onAgreePrivacyAndCapture() {
    this.setData({ privacyNeedAuth: false });
    this.startBleVitalsCapture();
  },

  async onBleCaptureTap() {
    if (this.data.vitalsCapture.active) return;
    try {
      await ensurePrivacyAuthorized();
      await this.startBleVitalsCapture();
    } catch (err) {
      console.warn('隐私授权未完成:', err);
      await this.refreshPrivacySetting();
      wx.showModal({
        title: '需要隐私授权',
        content: '使用蓝牙采集需先阅读并同意《用户隐私保护指引》。',
        confirmText: '查看指引',
        cancelText: '取消',
        success: (res) => {
          if (res.confirm) openPrivacyContract();
        }
      });
    }
  },

  // MAX30102 蓝牙采集 → 后端生理参数分析
  async startBleVitalsCapture() {
    if (this.data.vitalsCapture.active) return;

    this.setData({
      vitalsCapture: {
        active: true,
        progress: 0,
        statusText: '正在搜索 ZenPulse 设备…',
        done: false,
        heartRate: '',
        spo2: '',
        hrStatus: '',
        spo2Status: '',
        overallStatus: '',
        sampleCount: 0,
        previewPoints: [],
        alerts: [],
        limitations: []
      }
    });

    wx.showLoading({ title: '蓝牙采集中', mask: true });

    try {
      const app = getAppSafe();
      const connected = await bootstrapServer(app);
      if (!connected) {
        wx.showModal({
          title: '无法连接后端',
          content: '请先运行 python3 web_server.py，并在 config/env.js 配置局域网 IP。',
          showCancel: false
        });
        return;
      }

      const captured = await captureBleVitals(10, (progress) => {
        this.setData({
          'vitalsCapture.progress': progress,
          'vitalsCapture.statusText': `采集中 ${progress}% · 请保持腕部静止`
        });
      });

      this.setData({ 'vitalsCapture.statusText': '上传分析中…' });

      const result = await analyzeVitals(captured.ch1, {
        fs: captured.fs,
        samples_ch2: captured.ch2,
        source: 'max30102_ble'
      });

      const hr = Math.round(result.heart_rate || 0);
      const previewPoints = downsampleForPreview(captured.ch1);
      const captureAlerts = [...(result.alerts || [])];
      if (captured.channelMismatch) {
        const mm = captured.channelMismatch;
        captureAlerts.unshift(
          `双通道点数不一致（CH1 ${mm.ch1Len} / CH2 ${mm.ch2Len}），已对齐 ${mm.alignedTo} 点`
        );
      }

      this.setData({
        metrics: {
          ...this.data.metrics,
          heart_rate: hr ? String(hr) : this.data.metrics.heart_rate,
          pulse: hr ? String(hr) : this.data.metrics.pulse,
          spo2: result.spo2 ? String(result.spo2) : '',
          pulse_waveform: captured.ch1,
          max30102_samples_ch2: captured.ch2,
          pulse_fs: captured.fs,
          pulse_source: 'max30102_ble',
          vitals_assessment: result
        },
        vitalsCapture: {
          active: false,
          progress: 100,
          statusText: '采集完成',
          done: true,
          heartRate: hr ? String(hr) : '--',
          spo2: result.spo2 ? String(result.spo2) : '--',
          hrStatus: result.hr_status || '',
          spo2Status: result.spo2_status || '',
          overallStatus: result.overall_status || '',
          sampleCount: result.sample_count || captured.ch1.length,
          previewPoints,
          alerts: captureAlerts,
          limitations: result.limitations || []
        }
      });

      wx.showToast({
        title: result.overall_status || '采集完成',
        icon: 'success',
        duration: 2000
      });
    } catch (err) {
      console.error('蓝牙采集失败:', err);
      const banned = isPrivacyApiBannedError(err);
      this.setData({
        vitalsCapture: {
          active: false,
          progress: 0,
          statusText: '',
          done: false,
          heartRate: '',
          spo2: '',
          hrStatus: '',
          spo2Status: '',
          overallStatus: '',
          sampleCount: 0,
          previewPoints: [],
          alerts: [],
          limitations: []
        }
      });
      wx.showModal({
        title: banned ? '蓝牙权限未声明' : '采集失败',
        content: banned
          ? privacyBannedMessage()
          : (err && err.message) || '请打开蓝牙、授予权限并保持静止后重试',
        showCancel: false
      });
      if (banned) this.refreshPrivacySetting();
    } finally {
      wx.hideLoading();
    }
  },

  clearVitalsCapture() {
    this.setData({
      metrics: {
        ...this.data.metrics,
        pulse_waveform: [],
        max30102_samples_ch2: [],
        pulse_source: 'manual',
        spo2: '',
        vitals_assessment: null
      },
      vitalsCapture: {
        active: false,
        progress: 0,
        statusText: '',
        done: false,
        heartRate: '',
        spo2: '',
        hrStatus: '',
        spo2Status: '',
        overallStatus: '',
        sampleCount: 0,
        previewPoints: [],
        alerts: [],
        limitations: []
      }
    });
  },

  onLoad() {
    console.log('健康指标页面加载');
    this.refreshPrivacySetting();
  },

  onShow() {
    console.log('健康指标页面显示');
    this.refreshPrivacySetting();
  },
  
  onReady() {
    // 页面初次渲染完成时执行
    console.log('健康指标页面渲染完成');
  },
  
  onHide() {
    // 页面隐藏时执行
    console.log('健康指标页面隐藏');
  },
  
  onUnload() {
    // 页面卸载时执行
    console.log('健康指标页面卸载');
  },
  
  // 心率输入处理
  onHeartRateInput(e) {
    const value = e.detail.value;
    this.setData({
      'metrics.heart_rate': value
    });
  },
  
  // 脉搏输入处理
  onPulseInput(e) {
    const value = e.detail.value;
    this.setData({
      'metrics.pulse': value
    });
  },
  
  // 收缩压输入处理
  onSystolicInput(e) {
    const value = e.detail.value;
    this.setData({
      'metrics.systolic': value
    });
  },
  
  // 舒张压输入处理
  onDiastolicInput(e) {
    const value = e.detail.value;
    this.setData({
      'metrics.diastolic': value
    });
  },
  
  // 年龄输入处理
  onAgeInput(e) {
    const value = e.detail.value;
    this.setData({
      'metrics.age': value
    });
  },
  
  // 性别选择处理
  onGenderSelect(e) {
    const gender = e.currentTarget.dataset.gender;
    this.setData({
      'metrics.gender': gender
    });
  },
  
  // 随机生成健康指标
  getRandomMetrics() {
    console.log('随机生成健康指标');
    
    // 显示加载提示
    wx.showLoading({
      title: '生成中...',
      mask: true
    });
    
    // 调用API获取随机健康指标
    getHealthMetrics()
      .then(res => {
        console.log('获取随机健康指标成功:', res);
        
        // 更新数据
        this.setData({
          metrics: {
            heart_rate: res.heart_rate.toString(),
            pulse: res.pulse.toString(),
            systolic: res.systolic.toString(),
            diastolic: res.diastolic.toString(),
            age: Math.floor(Math.random() * 50 + 20).toString(),
            gender: Math.random() > 0.5 ? '男' : '女',
            pulse_waveform: [],
            max30102_samples_ch2: [],
            pulse_fs: BLE_DEFAULT_FS,
            pulse_source: 'manual',
            spo2: '',
            vitals_assessment: null
          },
          vitalsCapture: {
            active: false,
            progress: 0,
            statusText: '',
            done: false,
            heartRate: '',
            spo2: '',
            hrStatus: '',
            spo2Status: '',
            overallStatus: '',
            sampleCount: 0,
            previewPoints: [],
            alerts: [],
            limitations: []
          }
        });
        
        // 显示成功提示
        wx.showToast({
          title: '生成成功',
          icon: 'success',
          duration: 1000
        });
      })
      .catch(err => {
        console.error('获取随机健康指标失败:', err);
        const msg = (err && err.message) || '';
        wx.showToast({
          title: /无法连接|timeout/i.test(msg) ? '后端未连接，已用本地数据' : '生成失败，已用本地数据',
          icon: 'none',
          duration: 2500
        });
        this.generateLocalRandomMetrics();
      })
      .finally(() => {
        // 隐藏加载提示
        wx.hideLoading();
      });
  },
  
  // 本地随机生成健康指标
  generateLocalRandomMetrics() {
    console.log('本地随机生成健康指标');
    
    const randomMetrics = {
      heart_rate: Math.floor(Math.random() * 41 + 60).toString(),
      pulse: Math.floor(Math.random() * 41 + 60).toString(),
      systolic: Math.floor(Math.random() * 51 + 90).toString(),
      diastolic: Math.floor(Math.random() * 31 + 60).toString(),
      age: Math.floor(Math.random() * 50 + 20).toString(),
      gender: Math.random() > 0.5 ? '男' : '女',
      pulse_waveform: [],
      max30102_samples_ch2: [],
      pulse_fs: BLE_DEFAULT_FS,
      pulse_source: 'manual',
      spo2: '',
      vitals_assessment: null
    };

    this.setData({
      metrics: randomMetrics,
      vitalsCapture: {
        active: false,
        progress: 0,
        statusText: '',
        done: false,
        heartRate: '',
        spo2: '',
        hrStatus: '',
        spo2Status: '',
        overallStatus: '',
        sampleCount: 0,
        previewPoints: [],
        alerts: [],
        limitations: []
      }
    });
  },
  
  // 验证健康指标数据
  validateMetrics() {
    const { heart_rate, pulse, systolic, diastolic, age, gender } = this.data.metrics;
    
    // 检查必填项
    if (!heart_rate) {
      wx.showToast({ title: '请输入心率', icon: 'none' });
      return false;
    }
    
    if (!pulse) {
      wx.showToast({ title: '请输入脉搏', icon: 'none' });
      return false;
    }
    
    if (!systolic) {
      wx.showToast({ title: '请输入收缩压', icon: 'none' });
      return false;
    }
    
    if (!diastolic) {
      wx.showToast({ title: '请输入舒张压', icon: 'none' });
      return false;
    }
    
    if (!age) {
      wx.showToast({ title: '请输入年龄', icon: 'none' });
      return false;
    }
    
    if (!gender) {
      wx.showToast({ title: '请选择性别', icon: 'none' });
      return false;
    }
    
    // 检查数值范围
    const heartRateNum = parseInt(heart_rate);
    if (heartRateNum < 40 || heartRateNum > 180) {
      wx.showToast({ title: '心率数值超出合理范围', icon: 'none' });
      return false;
    }
    
    const pulseNum = parseInt(pulse);
    if (pulseNum < 40 || pulseNum > 180) {
      wx.showToast({ title: '脉搏数值超出合理范围', icon: 'none' });
      return false;
    }
    
    const systolicNum = parseInt(systolic);
    if (systolicNum < 60 || systolicNum > 200) {
      wx.showToast({ title: '收缩压数值超出合理范围', icon: 'none' });
      return false;
    }
    
    const diastolicNum = parseInt(diastolic);
    if (diastolicNum < 40 || diastolicNum > 120) {
      wx.showToast({ title: '舒张压数值超出合理范围', icon: 'none' });
      return false;
    }
    
    const ageNum = parseInt(age);
    if (ageNum < 0 || ageNum > 150) {
      wx.showToast({ title: '年龄数值超出合理范围', icon: 'none' });
      return false;
    }
    
    return true;
  },
  
  // 下一步
  nextStep() {
    console.log('下一步');
    console.log('当前健康指标数据:', this.data.metrics);
    
    // 验证数据
    if (!this.validateMetrics()) {
      return;
    }
    
    // 跳转到图片上传页面
    wx.navigateTo({
      url: '/pages/upload/upload',
      success: (res) => {
        console.log('跳转到图片上传页面成功');
        
        // 传递健康指标数据
        console.log('传递健康指标数据:', this.data.metrics);
        res.eventChannel.emit('passMetrics', {
          metrics: this.data.metrics
        });
      },
      fail: (err) => {
        console.error('跳转到图片上传页面失败:', err);
        wx.showToast({
          title: '跳转失败，请重试',
          icon: 'none',
          duration: 2000
        });
      }
    });
  },
  
  // 返回首页
  backToHome() {
    console.log('返回首页');
    
    wx.navigateBack({
      delta: 1,
      success: (res) => {
        console.log('返回首页成功');
      },
      fail: (err) => {
        console.error('返回首页失败:', err);
        // 如果返回失败，直接跳转到首页
        wx.redirectTo({
          url: '/pages/index/index'
        });
      }
    });
  },
  
  // 下拉刷新
  onPullDownRefresh() {
    console.log('下拉刷新');
    
    // 模拟刷新
    setTimeout(() => {
      wx.stopPullDownRefresh();
      wx.showToast({
        title: '刷新成功',
        icon: 'success',
        duration: 1000
      });
    }, 1000);
  }
});
