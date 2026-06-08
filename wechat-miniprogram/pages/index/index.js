// index.js
Page({ 
  data: { 
    // 页面数据 
  }, 
  
  onLoad() { 
    // 页面加载时执行 
    console.log('首页加载'); 
    
    // 检查网络状态 
    this.checkNetworkStatus(); 
    
    // 初始化数据 
    this.initData(); 
  }, 
  
  onShow() { 
    // 页面显示时执行 
    console.log('首页显示'); 
  }, 
  
  onReady() { 
    // 页面初次渲染完成时执行 
    console.log('首页渲染完成'); 
  }, 
  
  onHide() { 
    // 页面隐藏时执行 
    console.log('首页隐藏'); 
  }, 
  
  onUnload() { 
    // 页面卸载时执行 
    console.log('首页卸载'); 
  }, 
  
  // 检查网络状态 
  checkNetworkStatus() { 
    wx.getNetworkType({ 
      success: (res) => { 
        const networkType = res.networkType; 
        console.log('网络状态:', networkType); 
        
        if (networkType === 'none') { 
          wx.showToast({ 
            title: '网络连接失败，请检查网络设置', 
            icon: 'none', 
            duration: 2000 
          }); 
        } 
      }, 
      fail: (err) => { 
        console.error('获取网络状态失败:', err); 
      } 
    }); 
  }, 
  
  // 初始化数据 
  initData() { 
    // 可以在这里初始化页面数据 
    console.log('初始化数据'); 
  }, 
  
  // 开始诊断 
  startDiagnosis() { 
    console.log('开始诊断'); 
    
    // 跳转到健康指标页面 
    wx.navigateTo({ 
      url: '/pages/metrics/metrics', 
      success: (res) => { 
        console.log('跳转到健康指标页面成功'); 
      }, 
      fail: (err) => { 
        console.error('跳转到健康指标页面失败:', err); 
        wx.showToast({ 
          title: '跳转失败，请重试', 
          icon: 'none', 
          duration: 2000 
        }); 
      } 
    }); 
  }, 
  
  // 跳转到历史记录页面 
  goToHistory() { 
    console.log('跳转到历史记录页面'); 
    
    // 跳转到个人中心页面（历史记录在个人中心页面中） 
    wx.switchTab({ 
      url: '/pages/profile/profile', 
      success: (res) => { 
        console.log('跳转到个人中心页面成功'); 
      }, 
      fail: (err) => { 
        console.error('跳转到个人中心页面失败:', err); 
        wx.showToast({ 
          title: '跳转失败，请重试', 
          icon: 'none', 
          duration: 2000 
        }); 
      } 
    }); 
  }, 
  
  // 跳转到关于我们页面 
  goToAbout() { 
    console.log('跳转到关于我们页面'); 
    
    // 目前暂时显示一个对话框 
    wx.showModal({ 
      title: '关于我们', 
      content: '中医智能诊断系统 v1.0.0\n\n基于人工智能技术的中医诊断助手，\n\n功能包括：\n- 健康指标分析\n- 舌象分析\n- 面部分析\n- 眼部分析\n- 脉象分析\n- 中医诊断\n\n© 2026 中医智能诊断系统', 
      confirmText: '确定', 
      success: (res) => { 
        if (res.confirm) { 
          console.log('用户点击确定'); 
        } 
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
  }, 
  
  // 页面滚动到底部 
  onReachBottom() { 
    console.log('页面滚动到底部'); 
  }, 
  
  // 分享 
  onShareAppMessage() { 
    return { 
      title: '中医智能诊断系统', 
      path: '/pages/index/index', 
      imageUrl: '../../images/share.png' 
    }; 
  }, 
  
  // 分享到朋友圈 
  onShareTimeline() { 
    return { 
      title: '中医智能诊断系统', 
      imageUrl: '../../images/share.png' 
    }; 
  } 
}); 