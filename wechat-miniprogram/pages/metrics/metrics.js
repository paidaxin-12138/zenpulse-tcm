// metrics.js
import { getHealthMetrics } from '../../utils/api';

Page({
  data: {
    // 健康指标数据
    metrics: {
      heart_rate: '',
      pulse: '',
      systolic: '',
      diastolic: '',
      age: '',
      gender: ''
    }
  },
  
  onLoad() {
    // 页面加载时执行
    console.log('健康指标页面加载');
  },
  
  onShow() {
    // 页面显示时执行
    console.log('健康指标页面显示');
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
            age: Math.floor(Math.random() * 50 + 20).toString(), // 20-70岁随机年龄
            gender: Math.random() > 0.5 ? '男' : '女' // 随机性别
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
      heart_rate: Math.floor(Math.random() * 41 + 60).toString(), // 60-100
      pulse: Math.floor(Math.random() * 41 + 60).toString(), // 60-100
      systolic: Math.floor(Math.random() * 51 + 90).toString(), // 90-140
      diastolic: Math.floor(Math.random() * 31 + 60).toString(), // 60-90
      age: Math.floor(Math.random() * 50 + 20).toString(), // 20-70岁
      gender: Math.random() > 0.5 ? '男' : '女'
    };
    
    this.setData({
      metrics: randomMetrics
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
