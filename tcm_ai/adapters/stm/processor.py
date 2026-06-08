import socket
import time
import random
import numpy as np
import threading
import logging
from collections import deque
from scipy import signal
from typing import Dict, List, Optional, Tuple, Any

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler('stm_data_processor.log'),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)

class MAX30102Processor:
    """
    MAX30102传感器处理器，实现脉搏信号采集和把脉功能
    支持两个传感器同时检测并取平均值
    """
    
    def __init__(self, sampling_rate: float = 100.0):
        self.sampling_rate = sampling_rate
        self.pulse_data = []
        self.heart_rate = 75.0
        self.spo2 = 98.0
        self.pulse_waveform = []
        self.ac_data = []  # 交流分量（脉搏信号）
        self.dc_data = []  # 直流分量（基线）
        self.sensor1_data = {}
        self.sensor2_data = {}
        
        # 设计带通滤波器
        nyquist = 0.5 * sampling_rate
        low = 0.5 / nyquist
        high = 5.0 / nyquist
        self.b, self.a = signal.butter(2, [low, high], btype='band')
    
    def process_pulse_data(self, raw_data: List[int]) -> Dict[str, Any]:
        """
        处理单个MAX30102采集的原始数据
        
        Args:
            raw_data: MAX30102采集的原始数据
            
        Returns:
            处理后的脉搏数据
        """
        # 提取AC和DC分量
        self.ac_data, self.dc_data = self._extract_components(raw_data)
        
        # 计算心率和血氧
        self.heart_rate = self._calculate_heart_rate(self.ac_data)
        self.spo2 = self._calculate_spo2(self.ac_data, self.dc_data)
        
        # 生成脉搏波形
        self.pulse_waveform = self._generate_waveform(self.ac_data)
        
        # 把脉分析
        pulse_characteristics = self._analyze_pulse_characteristics()
        
        return {
            'heart_rate': self.heart_rate,
            'spo2': self.spo2,
            'pulse_characteristics': pulse_characteristics,
            'pulse_waveform': self.pulse_waveform,
            'timestamp': time.time()
        }
    
    def process_dual_sensor_data(self, sensor1_data: List[int], sensor2_data: List[int]) -> Dict[str, Any]:
        """
        处理两个MAX30102传感器采集的原始数据并取平均值
        
        Args:
            sensor1_data: 第一个MAX30102传感器采集的原始数据
            sensor2_data: 第二个MAX30102传感器采集的原始数据
            
        Returns:
            处理后的脉搏数据（平均值）
        """
        # 分别处理两个传感器的数据
        self.sensor1_data = self.process_pulse_data(sensor1_data)
        self.sensor2_data = self.process_pulse_data(sensor2_data)
        
        # 计算平均值
        avg_heart_rate = (self.sensor1_data['heart_rate'] + self.sensor2_data['heart_rate']) / 2
        avg_spo2 = (self.sensor1_data['spo2'] + self.sensor2_data['spo2']) / 2
        
        # 生成平均脉搏波形
        avg_pulse_waveform = []
        if self.sensor1_data['pulse_waveform'] and self.sensor2_data['pulse_waveform']:
            min_length = min(len(self.sensor1_data['pulse_waveform']), len(self.sensor2_data['pulse_waveform']))
            for i in range(min_length):
                avg_value = (self.sensor1_data['pulse_waveform'][i] + self.sensor2_data['pulse_waveform'][i]) / 2
                avg_pulse_waveform.append(avg_value)
        
        # 综合分析脉搏特征
        pulse_characteristics = self._analyze_dual_pulse_characteristics()
        
        return {
            'heart_rate': round(avg_heart_rate, 1),
            'spo2': round(avg_spo2, 1),
            'pulse_characteristics': pulse_characteristics,
            'pulse_waveform': avg_pulse_waveform,
            'sensor1_data': self.sensor1_data,
            'sensor2_data': self.sensor2_data,
            'timestamp': time.time()
        }
    
    def _extract_components(self, raw_data: List[int]) -> Tuple[List[float], List[float]]:
        """
        提取AC和DC分量
        """
        ac_data = []
        dc_data = []
        
        # 简单的高通滤波提取AC分量（脉搏信号）
        if len(raw_data) > 1:
            dc = np.mean(raw_data)
            for value in raw_data:
                ac = value - dc
                ac_data.append(ac)
                dc_data.append(dc)
        
        return ac_data, dc_data
    
    def _calculate_heart_rate(self, ac_data: List[float]) -> float:
        """
        计算心率
        """
        if len(ac_data) < self.sampling_rate * 2:  # 至少2秒数据
            return 75.0
        
        # 应用滤波器
        filtered = signal.filtfilt(self.b, self.a, ac_data)
        
        # 检测峰值
        peaks = self._detect_peaks_improved(filtered)
        
        # 根据峰值间隔计算心率
        if len(peaks) >= 2:
            peak_intervals = []
            for i in range(1, len(peaks)):
                interval = peaks[i] - peaks[i-1]
                peak_intervals.append(interval)
            
            if peak_intervals:
                avg_interval = np.mean(peak_intervals)
                heart_rate = 60.0 / (avg_interval / self.sampling_rate)
                return round(max(40, min(180, heart_rate)), 1)
        
        return 75.0
    
    def _calculate_spo2(self, ac_data: List[float], dc_data: List[float]) -> float:
        """
        计算血氧饱和度
        """
        if not ac_data or not dc_data:
            return 98.0
        
        # 简单的血氧计算（实际应用中需要更复杂的算法）
        ac_ratio = np.std(ac_data) / np.mean(ac_data) if np.mean(ac_data) > 0 else 0
        spo2 = 100.0 - (ac_ratio * 10.0)
        return round(max(70, min(100, spo2)), 1)
    
    def _detect_peaks(self, data: List[float]) -> List[int]:
        """
        检测信号峰值
        """
        peaks = []
        threshold = np.mean(data) + np.std(data) * 0.5
        
        for i in range(1, len(data) - 1):
            if data[i] > threshold and data[i] > data[i-1] and data[i] > data[i+1]:
                peaks.append(i)
        
        return peaks
    
    def _detect_peaks_improved(self, data: List[float]) -> List[int]:
        """
        改进的峰值检测算法
        """
        peaks = []
        
        # 使用更严格的阈值
        threshold = np.mean(data) + np.std(data) * 0.7
        
        # 计算一阶和二阶导数
        if len(data) > 2:
            dy = np.diff(data)
            d2y = np.diff(dy)
            
            for i in range(1, len(dy) - 1):
                # 寻找满足条件的峰值
                if (data[i+1] > threshold and 
                    dy[i] > 0 and dy[i+1] < 0 and 
                    d2y[i] < -0.1):
                    peaks.append(i+1)
        
        return peaks
    
    def _generate_waveform(self, ac_data: List[float]) -> List[float]:
        """
        生成脉搏波形
        """
        return ac_data
    
    def _analyze_pulse_characteristics(self) -> Dict[str, str]:
        """
        分析脉搏特征，实现中医把脉功能
        """
        characteristics = {
            'pulse_shape': '正常',
            'pulse_strength': '适中',
            'pulse_rate': '正常',
            'tcm_interpretation': '平和脉'
        }
        
        # 根据心率分析
        if self.heart_rate < 60:
            characteristics['pulse_rate'] = '过缓'
            characteristics['tcm_interpretation'] = '迟脉'
        elif self.heart_rate > 100:
            characteristics['pulse_rate'] = '过速'
            characteristics['tcm_interpretation'] = '数脉'
        
        # 根据脉搏强度分析（这里使用简化的方法）
        if self.ac_data:
            pulse_strength = np.std(self.ac_data)
            if pulse_strength < 100:
                characteristics['pulse_strength'] = '虚弱'
                characteristics['tcm_interpretation'] = '虚脉'
            elif pulse_strength > 500:
                characteristics['pulse_strength'] = '强劲'
                characteristics['tcm_interpretation'] = '实脉'
        
        return characteristics
    
    def _analyze_dual_pulse_characteristics(self) -> Dict[str, str]:
        """
        分析两个传感器的脉搏特征，实现综合中医把脉功能
        """
        # 获取两个传感器的特征
        sensor1_char = self.sensor1_data.get('pulse_characteristics', {})
        sensor2_char = self.sensor2_data.get('pulse_characteristics', {})
        
        # 综合分析
        characteristics = {
            'pulse_shape': '正常',
            'pulse_strength': '适中',
            'pulse_rate': '正常',
            'tcm_interpretation': '平和脉',
            'consistency': '一致'
        }
        
        # 分析脉搏速率一致性
        rate1 = sensor1_char.get('pulse_rate', '正常')
        rate2 = sensor2_char.get('pulse_rate', '正常')
        if rate1 != rate2:
            characteristics['consistency'] = '速率不一致'
        characteristics['pulse_rate'] = rate1 if rate1 != '正常' else rate2
        
        # 分析脉搏强度一致性
        strength1 = sensor1_char.get('pulse_strength', '适中')
        strength2 = sensor2_char.get('pulse_strength', '适中')
        if strength1 != strength2:
            characteristics['consistency'] = '强度不一致'
        characteristics['pulse_strength'] = strength1 if strength1 != '适中' else strength2
        
        # 综合中医诊断
        tcm1 = sensor1_char.get('tcm_interpretation', '平和脉')
        tcm2 = sensor2_char.get('tcm_interpretation', '平和脉')
        
        if tcm1 != '平和脉' and tcm2 != '平和脉':
            if tcm1 == tcm2:
                characteristics['tcm_interpretation'] = tcm1
            else:
                # 如果两个传感器的诊断不同，优先考虑异常的诊断
                abnormal_pulses = ['迟脉', '数脉', '虚脉', '实脉']
                for pulse_type in abnormal_pulses:
                    if pulse_type in [tcm1, tcm2]:
                        characteristics['tcm_interpretation'] = pulse_type
                        break
        elif tcm1 != '平和脉':
            characteristics['tcm_interpretation'] = tcm1
        elif tcm2 != '平和脉':
            characteristics['tcm_interpretation'] = tcm2
        
        return characteristics

class STMDataProcessor:
    def __init__(self, host: str = '192.168.1.100', port: int = 8080, timeout: float = 5.0, buffer_size: int = 500, process_interval: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.buffer_size = buffer_size
        self.process_interval = process_interval
        self.socket = None
        self.is_connected = False
        self.max30102_processor = MAX30102Processor()
        
        # 新增：线程和缓冲区管理
        self.buffer1 = deque(maxlen=buffer_size)   # 传感器1原始数据
        self.buffer2 = deque(maxlen=buffer_size)   # 传感器2原始数据
        self.latest_result = None
        self.running = False
        self.recv_thread = None
        self.timer = None
        self.lock = threading.Lock()
        self.last_reconnect_attempt = 0
    
    def connect(self) -> bool:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            self.is_connected = True
            self.running = True
            self.recv_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.recv_thread.start()
            self._start_timer()  # 启动定时器
            logger.info(f"成功连接到ESP32 WiFi: {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"WiFi连接失败: {e}")
            self.is_connected = False
            return False
    
    def _start_timer(self):
        """
        启动定时器，定期处理缓冲区数据
        """
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.process_interval, self._process_buffers)
        self.timer.daemon = True
        self.timer.start()
    
    def _process_buffers(self):
        """
        定期处理缓冲区数据
        """
        with self.lock:
            if len(self.buffer1) >= 100 and len(self.buffer2) >= 100:  # 至少需要一定点数
                data1 = list(self.buffer1)[-self.buffer_size:]
                data2 = list(self.buffer2)[-self.buffer_size:]
                result = self.max30102_processor.process_dual_sensor_data(data1, data2)
                self.latest_result = result
        self._start_timer()  # 重新启动定时器
    
    def disconnect(self) -> None:
        self.running = False
        if self.timer:
            self.timer.cancel()
        if self.recv_thread:
            self.recv_thread.join(timeout=1.0)
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            finally:
                self.socket = None
                self.is_connected = False
    
    def _receive_loop(self):
        buffer = ""
        while self.running and self.is_connected:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    break
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if line:
                        self._handle_line(line)
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"WiFi数据接收失败: {e}")
                break
        self.is_connected = False
    
    def _handle_line(self, line: str):
        """处理一行数据，格式：CH1:123,CH2:124"""
        # 解析并追加数据时加锁
        with self.lock:
            # 解析两个通道的值
            parts = line.split(',')
            for part in parts:
                if ':' in part:
                    key, val = part.split(':', 1)
                    try:
                        val = int(val.strip())
                        if key.strip().upper() == 'CH1':
                            self.buffer1.append(val)
                        elif key.strip().upper() == 'CH2':
                            self.buffer2.append(val)
                    except:
                        pass
    
    def read_pulse_data(self) -> Optional[Dict[str, Any]]:
        """
        读取并处理脉搏数据，支持两个MAX30102传感器
        """
        if not self.is_connected:
            # 尝试重连（限制频率）
            if time.time() - self.last_reconnect_attempt > 5:
                self.last_reconnect_attempt = time.time()
                self.connect()
            return self._generate_simulation_pulse_data()
        elif self.latest_result is None:
            return self._generate_simulation_pulse_data()
        return self.latest_result
    
    def _generate_simulation_pulse_data(self) -> Dict[str, Any]:
        """
        生成模拟脉搏数据，用于测试
        """
        # 生成模拟的传感器数据
        def generate_sensor_data():
            base_value = 1000
            data = []
            for i in range(100):
                # 生成带有正弦波的模拟数据
                value = base_value + 300 * abs(np.sin(i * 0.1)) + random.uniform(-50, 50)
                data.append(int(value))
            return data
        
        sensor1_data = generate_sensor_data()
        sensor2_data = generate_sensor_data()
        
        # 使用MAX30102Processor处理模拟数据
        return self.max30102_processor.process_dual_sensor_data(sensor1_data, sensor2_data)
