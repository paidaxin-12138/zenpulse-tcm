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
from tcm_ai.domain.pulse.analyzer import PpgWaveformAnalyzer
from tcm_ai.domain.pulse.synthetic import synthetic_pulse_waveform

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
        self._analyzer = PpgWaveformAnalyzer()
    
    def _extract_sensor_metrics(self, raw_data: List[int]) -> Dict[str, Any]:
        """仅提取心率/血氧等轻量指标，不跑完整脉象分析。"""
        ac_data, dc_data = self._extract_components(raw_data)
        return {
            'heart_rate': self._calculate_heart_rate(ac_data),
            'spo2': self._calculate_spo2(ac_data, dc_data),
            'pulse_waveform': raw_data,
        }

    def process_pulse_data(self, raw_data: List[int]) -> Dict[str, Any]:
        """
        处理单个MAX30102采集的原始数据
        
        Args:
            raw_data: MAX30102采集的原始数据
            
        Returns:
            处理后的脉搏数据
        """
        metrics = self._extract_sensor_metrics(raw_data)
        self.ac_data, self.dc_data = self._extract_components(raw_data)
        self.heart_rate = metrics['heart_rate']
        self.spo2 = metrics['spo2']
        self.pulse_waveform = self._generate_waveform(self.ac_data)

        return {
            'heart_rate': metrics['heart_rate'],
            'spo2': metrics['spo2'],
            'pulse_waveform': raw_data,
            'fs': self.sampling_rate,
            'timestamp': time.time()
        }
    
    def process_dual_sensor_data(
        self,
        sensor1_data: List[int],
        sensor2_data: List[int],
        imu: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        处理两个MAX30102传感器采集的原始数据并取平均值
        
        Args:
            sensor1_data: 第一个MAX30102传感器采集的原始数据
            sensor2_data: 第二个MAX30102传感器采集的原始数据
            
        Returns:
            处理后的脉搏数据（平均值）
        """
        # 分别提取两个传感器的轻量指标
        self.sensor1_data = self.process_pulse_data(sensor1_data)
        self.sensor2_data = self.process_pulse_data(sensor2_data)
        
        # 计算平均值
        avg_heart_rate = (self.sensor1_data['heart_rate'] + self.sensor2_data['heart_rate']) / 2
        avg_spo2 = (self.sensor1_data['spo2'] + self.sensor2_data['spo2']) / 2
        
        merged_raw: List[int] = []
        if sensor1_data and sensor2_data:
            min_length = min(len(sensor1_data), len(sensor2_data))
            for i in range(min_length):
                merged_raw.append(int((sensor1_data[i] + sensor2_data[i]) / 2))
        elif sensor1_data:
            merged_raw = list(sensor1_data)
        else:
            merged_raw = list(sensor2_data)

        analysis = self._analyzer.analyze_from_waveform(
            merged_raw,
            fs=self.sampling_rate,
            imu=imu,
            source="stm",
            capability_level="L1",
        )

        return {
            'heart_rate': analysis.waveform_stats.get('heart_rate', round(avg_heart_rate, 1)),
            'spo2': round(avg_spo2, 1),
            'pulse_waveform': merged_raw,
            'fs': self.sampling_rate,
            'pulse_analysis': analysis.to_dict(),
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
    
    def _generate_simulation_raw(self, duration_sec: float = 15.0) -> List[int]:
        waveform = synthetic_pulse_waveform(duration_sec=duration_sec, fs=self.sampling_rate)
        return [int(v) for v in waveform]


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
        self._imu_buffer: deque = deque(maxlen=buffer_size)
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
                imu_payload = None
                if self._imu_buffer:
                    imu_payload = {
                        'acc_x': [s.get('ax', 0) for s in self._imu_buffer],
                        'acc_y': [s.get('ay', 0) for s in self._imu_buffer],
                        'acc_z': [s.get('az', 0) for s in self._imu_buffer],
                        'fs': self.max30102_processor.sampling_rate,
                    }
                result = self.max30102_processor.process_dual_sensor_data(
                    data1,
                    data2,
                    imu=imu_payload,
                )
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
        """处理一行数据。v0: CH1:123,CH2:124  v2: TS:...,CH1:...,CH2:...,AX:..."""
        with self.lock:
            imu_sample: Dict[str, int] = {}
            parts = line.split(',')
            for part in parts:
                if ':' not in part:
                    continue
                key, val = part.split(':', 1)
                key = key.strip().upper()
                try:
                    num = int(val.strip())
                except ValueError:
                    continue
                if key == 'CH1':
                    self.buffer1.append(num)
                elif key == 'CH2':
                    self.buffer2.append(num)
                elif key in ('AX', 'AY', 'AZ'):
                    imu_sample[key.lower()] = num
            if imu_sample:
                self._imu_buffer.append(imu_sample)
    
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
        sensor1_data = self.max30102_processor._generate_simulation_raw()
        sensor2_data = self.max30102_processor._generate_simulation_raw()
        
        # 使用MAX30102Processor处理模拟数据
        return self.max30102_processor.process_dual_sensor_data(sensor1_data, sensor2_data)
