// upload.js
import { wxDiagnose, bootstrapServer } from '../../utils/api';
import { getAuthHeaders } from '../../utils/auth';

Page({
  data: {
    // 图片数据
    images: {
      tongue: '',
      face: '',
      eye: ''
    },
    // 健康指标数据
    metrics: {},
    // 诊断状态
    isDiagnosing: false
  },
  
  onLoad(options) {
    // 页面加载时执行
    console.log('图片上传页面加载');
    console.log('页面加载时的options:', options);
    
    // 接收健康指标数据
    const eventChannel = this.getOpenerEventChannel();
    console.log('获取事件通道:', eventChannel);
    if (eventChannel) {
      console.log('事件通道存在，开始监听passMetrics事件');
      eventChannel.on('passMetrics', (data) => {
        console.log('接收到健康指标数据:', data);
        console.log('接收到的metrics数据:', data.metrics);
        this.setData({
          metrics: data.metrics
        });
        console.log('设置健康指标数据后:', this.data.metrics);
      });
    } else {
      console.log('事件通道不存在，无法接收健康指标数据');
    }
    
    // 初始化数据
    this.initData();
  },
  
  onShow() {
    // 页面显示时执行
    console.log('图片上传页面显示');
    console.log('页面显示时健康指标数据:', this.data.metrics);
  },
  
  onReady() {
    // 页面初次渲染完成时执行
    console.log('图片上传页面渲染完成');
  },
  
  onHide() {
    // 页面隐藏时执行
    console.log('图片上传页面隐藏');
  },
  
  onUnload() {
    // 页面卸载时执行
    console.log('图片上传页面卸载');
  },
  
  // 初始化数据
  initData() {
    console.log('初始化数据');
  },
  
  // 选择舌苔图片
  chooseTongueImage() {
    this.chooseImage('tongue');
  },
  
  // 选择面部图片
  chooseFaceImage() {
    this.chooseImage('face');
  },
  
  // 选择眼部图片
  chooseEyeImage() {
    this.chooseImage('eye');
  },
  
  // 选择图片通用方法
  chooseImage(type) {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        console.log('选择图片成功:', res);
        
        const tempFilePaths = res.tempFiles[0].tempFilePath;
        console.log('原始图片路径:', tempFilePaths);
        console.log('原始图片大小:', res.tempFiles[0].size);
        
        // 进一步压缩图片
        wx.compressImage({
          src: tempFilePaths,
          quality: 50, // 压缩质量，取值范围0-100
          success: (compressRes) => {
            console.log('图片压缩成功:', compressRes);
            console.log('压缩后图片路径:', compressRes.tempFilePath);
            
            // 更新图片数据
            this.setData({
              [`images.${type}`]: compressRes.tempFilePath
            });
            
            // 显示成功提示
            wx.showToast({
              title: '图片上传成功',
              icon: 'success',
              duration: 1000
            });
          },
          fail: (compressErr) => {
            console.error('图片压缩失败:', compressErr);
            // 压缩失败时使用原始图片
            this.setData({
              [`images.${type}`]: tempFilePaths
            });
            
            // 显示成功提示
            wx.showToast({
              title: '图片上传成功',
              icon: 'success',
              duration: 1000
            });
          }
        });
      },
      fail: (err) => {
        console.error('选择图片失败:', err);
        wx.showToast({
          title: '选择图片失败，请重试',
          icon: 'none',
          duration: 2000
        });
      }
    });
  },
  
  // 预览图片
  previewImage(e) {
    const image = e.currentTarget.dataset.image;
    wx.previewImage({
      urls: [image],
      success: (res) => {
        console.log('预览图片成功');
      },
      fail: (err) => {
        console.error('预览图片失败:', err);
      }
    });
  },
  
  // 删除图片
  deleteImage(e) {
    const type = e.currentTarget.dataset.type;
    
    wx.showModal({
      title: '删除图片',
      content: '确定要删除这张图片吗？',
      success: (res) => {
        if (res.confirm) {
          console.log('用户确认删除图片:', type);
          
          // 更新图片数据
          this.setData({
            [`images.${type}`]: ''
          });
          
          // 显示成功提示
          wx.showToast({
            title: '图片删除成功',
            icon: 'success',
            duration: 1000
          });
        } else if (res.cancel) {
          console.log('用户取消删除图片');
        }
      }
    });
  },
  
  // 验证图片数据
  validateImages() {
    const { tongue, face, eye } = this.data.images;
    
    // 至少需要上传一张图片
    if (!tongue && !face && !eye) {
      wx.showToast({
        title: '请至少上传一张图片',
        icon: 'none',
        duration: 2000
      });
      return false;
    }
    
    return true;
  },
  
  // 准备诊断数据
  prepareDiagnosisData() {
    const { images, metrics } = this.data;
    console.log('准备诊断数据 - 健康指标:', metrics);
    const formData = {
      heartRate: parseInt(metrics.heart_rate),
      pulse: parseInt(metrics.pulse),
      systolic: parseInt(metrics.systolic),
      diastolic: parseInt(metrics.diastolic),
      age: parseInt(metrics.age),
      gender: metrics.gender
    };
    
    const files = {
      tongueImage: images.tongue,
      faceImage: images.face,
      eyeImage: images.eye
    };
    
    console.log('准备诊断数据 - 表单数据:', formData);
    console.log('准备诊断数据 - 文件数据:', files);
    return { formData, files };
  },
  
  // 开始诊断
  async startDiagnosis() {
    console.log('开始诊断');
    console.log('当前健康指标数据:', this.data.metrics);
    
    // 验证图片数据
    if (!this.validateImages()) {
      return;
    }
    
    // 验证健康指标数据
    if (!this.data.metrics || !this.data.metrics.heart_rate) {
      console.log('健康指标数据验证失败:', this.data.metrics);
      wx.showToast({
        title: '请先输入健康指标',
        icon: 'none',
        duration: 2000
      });
      return;
    }
    
    // 显示加载提示
    wx.showLoading({
      title: '诊断中...',
      mask: true
    });
    
    this.setData({ isDiagnosing: true });
    
    try {
      const app = getApp();
      const connected = await bootstrapServer(app);
      if (!connected) {
        wx.showModal({
          title: '无法连接后端',
          content: '请先在电脑运行 python3 web_server.py。真机调试请在 config/env.js 填写局域网 IP。',
          showCancel: false
        });
        return;
      }

      // 准备诊断数据
      const { formData, files } = this.prepareDiagnosisData();
      console.log('诊断数据:', { formData, files });
      
      // 调用诊断API
      const result = await wxDiagnose(formData, files, getAuthHeaders());
      console.log('诊断结果:', result);
      
      // 保存诊断结果到本地存储，作为备份
      wx.setStorageSync('lastDiagnosisResult', result);
      wx.setStorageSync('lastDiagnosisContext', {
        metrics: this.data.metrics,
        date: new Date().toISOString()
      });
      console.log('诊断结果已保存到本地存储');
      
      // 跳转到诊断结果页面
      wx.navigateTo({
        url: '/pages/result/result',
        success: (res) => {
          console.log('跳转到诊断结果页面成功');
          
          // 传递诊断结果数据
          try {
            if (res.eventChannel && typeof res.eventChannel.emit === 'function') {
              console.log('事件通道存在且有emit方法，开始传递诊断结果数据');
              res.eventChannel.emit('passDiagnosisResult', {
                result: result
              });
              console.log('诊断结果数据传递成功');
            } else {
              console.log('事件通道不存在或没有emit方法，无法传递诊断结果数据');
            }
          } catch (error) {
            console.error('传递诊断结果数据时出错:', error);
          }
        },
        fail: (err) => {
          console.error('跳转到诊断结果页面失败:', err);
          wx.showToast({
            title: '跳转失败，请重试',
            icon: 'none',
            duration: 2000
          });
        }
      });
    } catch (err) {
      console.error('诊断失败:', err);
      const msg = (err && err.message) || (err && err.errMsg) || '';
      let title = '诊断失败，请重试';
      if (/timeout/i.test(msg)) {
        title = '诊断超时，请检查网络或稍后重试';
      } else if (/无法连接|连接服务器/i.test(msg)) {
        title = '无法连接服务器，请启动后端';
      } else if (msg && msg.length < 40) {
        title = msg;
      }
      wx.showModal({
        title: '诊断未完成',
        content: msg || title,
        showCancel: false
      });
    } finally {
      this.setData({ isDiagnosing: false });
      // 确保hideLoading被调用
      try {
        wx.hideLoading();
      } catch (error) {
        console.error('隐藏加载提示时出错:', error);
      }
    }
  },
  
  // 返回上一步
  backToMetrics() {
    console.log('返回上一步');
    
    wx.navigateBack({
      delta: 1,
      success: (res) => {
        console.log('返回健康指标页面成功');
      },
      fail: (err) => {
        console.error('返回健康指标页面失败:', err);
        // 如果返回失败，直接跳转到健康指标页面
        wx.redirectTo({
          url: '/pages/metrics/metrics'
        });
      }
    });
  },
  
  // 返回首页
  backToHome() {
    console.log('返回首页');
    
    wx.navigateBack({
      delta: 2,
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
