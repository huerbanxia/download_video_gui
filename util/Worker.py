from contextlib import closing
from PyQt5.QtCore import *
from util.HttpClient import HttpClient
import os
from util.SizeUtil import SizeUtil


class Worker(QThread):
    # 下载进度的在table中的列索引值 用以回调更新表格
    start_column_num = 5

    tableViewSign = pyqtSignal(list)

    startSign = pyqtSignal()

    globalInfoSign = pyqtSignal(str)

    def __init__(self, info=None, save_path='', data_id='', proxy_path='127.0.0.1:1080'):
        super().__init__()
        self.info = info
        self.save_path = save_path
        self.data_id = data_id

        self.http_client = HttpClient(proxy_path=proxy_path)

    def __del__(self):
        self.wait()

    def run(self):
        self.globalInfoSign.emit("下载任务开始")
        complex_flag = False
        try:
            with closing(self.http_client.get(self.info['uri'], stream=True, is_proxies=True, timeout=5)) as response:
                chunk_size = 1024
                content_size = int(response.headers['content-length'])
                date_count = 0
                # 若路径不存在 就创建
                if not os.path.lexists(self.save_path):
                    os.mkdir(self.save_path)
                # 拼接文件地址
                file_path = self.save_path + self.info['title'] + '.mp4'
                if os.path.lexists(file_path):
                    size = os.path.getsize(file_path)
                    if size == content_size:
                        self.globalInfoSign.emit('文件已下载完成:' + file_path)
                        args = [
                            self.data_id, self.start_column_num, "100.000%",
                            "%s/%s" % (SizeUtil.hum_convert(size), SizeUtil.hum_convert(content_size))
                        ]
                        self.tableViewSign.emit(args)
                        self.startSign.emit()
                        complex_flag = True
                    else:
                        # 文件下载不完整，目前不支持断点续传，直接删除文件
                        os.remove(file_path)
                # 判断文件是否已下载完整，若已下载则直接返回
                if complex_flag:
                    return
                try:
                    file_path_temp = self.save_path + self.info['title'] + '.mp4' + '.temp'
                    with open(file_path_temp, "wb") as file:
                        for data in response.iter_content(chunk_size=chunk_size):
                            file.write(data)
                            date_count = date_count + len(data)
                            now_jd = (date_count / content_size) * 100
                            # print("\r 文件下载进度: %d%%(%d/%d) - %s" % (
                            #     now_jd, date_count, content_size, file_path))
                            date_count_str = SizeUtil.hum_convert(date_count)
                            content_size_str = SizeUtil.hum_convert(content_size)
                            args = [
                                self.data_id, self.start_column_num, "%.3f%%" % now_jd,
                                                                   "%s/%s" % (date_count_str, content_size_str)
                            ]
                            self.tableViewSign.emit(args)
                    # 文件重命名
                    os.rename(file_path_temp, file_path)
                except Exception as e:
                    args = [
                        self.data_id, self.start_column_num, "下载出错" + str(e), "%d/%d" % (date_count, content_size)
                    ]
                    # 删除文件
                    os.remove(file_path_temp)
                    self.tableViewSign.emit(args)

            print("任务完成 开启新任务")
            self.startSign.emit()
        except Exception as e:
            print(e)
