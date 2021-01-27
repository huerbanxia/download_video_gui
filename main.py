import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtWidgets import QMessageBox, QHeaderView, QMenu, QWidget
from FormView import Ui_dialog
from util.HttpClient import HttpClient
from util.Worker import Worker
import configparser
import os
from urllib import parse
import uuid


class MainForm(QWidget, Ui_dialog):

    def __init__(self):
        # 视图处理
        super(MainForm, self).__init__()
        self.setupUi(self)
        self.icon = QIcon(':img/favicon_small.ico')
        # 设置图标
        self.setWindowIcon(self.icon)

        # ================================ 控件初始化赋值 ================================
        # 初始化配置文件
        self.conf_flag = False
        self.__init_config()
        # 解析url文本框
        if self.conf_flag:
            # url地址
            self.lineEdit.setText(self.conf.get('global', 'url'))
            # 代理地址文本框
            self.proxyPathEdit.setText(self.conf.get('global', 'proxy_path'))
            # 下载线程数文本框
            self.downloadTaskNumEdit.setText(self.conf.get('global', 'download_task_num'))
            # 存储位置文本框
            self.savePathEdit.setText(self.conf.get('global', 'save_path_edit'))
        else:
            # url地址
            self.lineEdit.setText('https://ecchi.iwara.tv/users/Dyson000/videos')
            # 代理地址文本框
            self.proxyPathEdit.setText('127.0.0.1:1080')
            # 下载线程数文本框
            self.downloadTaskNumEdit.setText('1')
            # 存储位置文本框
            self.savePathEdit.setText('D:/test')
        # 初始化表格
        self.__init_table()

        # ================================ 数据初始化赋值 ================================
        # 列表页面url
        self.url = ''
        # 声明解析后的数据信息集合
        self.video_info_list = []

        self.task_data = []
        self.task_list = []
        # 声明请求工具类
        self.http_client = HttpClient(proxy_path=self.proxyPathEdit.text())
        # 初始化解析线程池
        self.__parse_thread_pool = ThreadPoolExecutor(max_workers=20,
                                                      thread_name_prefix="python_comic_parse_")
        # 声明下载线程池
        self.__download_thread_pool = None
        # 声明线程锁
        self.lock = threading.Lock()
        # 上次打开的保存位置
        self.last_save_path = 'C:\\'

    # ================================ 按钮点击事件重写 ================================
    # 解析按钮
    def parsing_btn_click(self):
        # 获取输入网址
        text = self.lineEdit.text()
        # 拼接参数
        if "?" in text:
            text = text + "&language=zh-hans"
        else:
            text = text + "?language=zh-hans"
        # 清空视频信息
        self.video_info_list = []
        # 初始化表格
        self.__init_table()
        # 启用多线程解析视频信息并跟新视图
        task = threading.Thread(target=self.__get_list_info, args=[text])
        task.start()

    # 批量下载按钮
    def batch_download_btn_click(self):
        # # 获取同时下载个数
        num = self.downloadTaskNumEdit.text()
        # 获取保存路径
        save_path = self.savePathEdit.text() + '/'
        # 存储进程列表 防止局部变量覆盖后线程终止
        self.task_list = []
        # 遍历解析出的视频数据 向线程池提交下载任务
        if len(self.video_info_list) > 0:
            for index, info in enumerate(self.video_info_list):
                if index < int(num):
                    # 实例化多线程对象
                    thread = Worker(info=info, save_path=save_path, data_id=info['id'],
                                    proxy_path=self.proxyPathEdit.text())
                    # 信号与槽函数的连接
                    thread.tableViewSign.connect(self.__update_table_item)
                    # 线程开启信号连接
                    thread.startSign.connect(self.__start_download)
                    # 信息更新连接
                    thread.globalInfoSign.connect(self.__change_info_label)
                    thread.start()
                    self.task_list.append(thread)
                else:
                    # 设置批量下载按钮可点击
                    self.batchDownloadButton.setDisabled(True)
                    info.setdefault('index', index)
                    self.task_data.append(info)

    # 下载一个按钮
    def single_download_btn_click(self):
        self.__start_download()

    # 选择保存位置按钮
    def select_file_dir_btn(self):
        # 起始路径 上次选择的位置
        directory = QtWidgets.QFileDialog.getExistingDirectory(None, "请选择存储位置", self.last_save_path)
        if directory:
            self.last_save_path = directory
        self.savePathEdit.setText(directory)

    # 关闭按钮执行方法
    def closeEvent(self, close_event):
        # 创建一个问答框，注意是Question
        box = QMessageBox(QMessageBox.Question, '退出', '确定保存配置并退出?')
        # 添加按钮，可用中文
        yes = box.addButton('保存配置并退出', QMessageBox.YesRole)
        no = box.addButton('直接退出', QMessageBox.NoRole)
        cancel = box.addButton('取消', QMessageBox.RejectRole)
        # 设置消息框中内容前面的图标
        box.setWindowIcon(self.icon)
        # 设置消息框的位置，大小无法设置
        # box.setGeometry(500, 500, 0, 0)
        # 显示该问答框
        box.exec_()
        # 判断分支选择
        if box.clickedButton() == yes:
            self._save_config_to_file()
            close_event.accept()
        elif box.clickedButton() == no:
            close_event.accept()
        else:
            close_event.ignore()

    def _save_config_to_file(self):
        # 确定关闭 写入当前配置
        if not self.conf.has_section("global"):
            self.conf.add_section("global")
        # 写入配置
        self.conf.set("global", "url", parse.unquote(self.lineEdit.text()))
        self.conf.set("global", "proxy_path", self.proxyPathEdit.text())
        self.conf.set("global", "download_task_num", self.downloadTaskNumEdit.text())
        self.conf.set("global", "save_path_edit", self.savePathEdit.text())
        # 保存到文件
        self.conf.write(open("config.ini", "w", encoding='utf-8'))

    # ================================ 内部调用方法 ================================
    # 初始化表格
    def __init_table(self):
        self.tableView.model = QStandardItemModel(0, 6)
        self.tableView.model.setHorizontalHeaderLabels(["主键", "标题", "发布顺序", "like数", "观看数", "下载进度", "大小"])
        # 表头列宽自动分配
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # 水平方向标签拓展剩下的窗口部分，填满表格
        self.tableView.horizontalHeader().setStretchLastSection(True)
        # 设置行号列宽度 对齐方式
        self.tableView.verticalHeader().setFixedWidth(50)
        self.tableView.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        # 更新表格
        self.tableView.setModel(self.tableView.model)
        # 设置标题宽度
        self.tableView.setColumnWidth(1, 350)
        # 设置发布顺序宽度
        self.tableView.setColumnWidth(2, 60)
        # 设置喜爱数宽度
        self.tableView.setColumnWidth(3, 50)
        # 隐藏id列
        self.tableView.setColumnHidden(0, True)

        self.tableView.setSortingEnabled(True)

        # 初始化右键菜单
        self.tableView.customContextMenuRequested.connect(self.__show_table_right_menu)
        self.right_menu = QMenu()
        self.table_menu_action_del = self.right_menu.addAction("删除行")
        self.table_menu_action_re_download = self.right_menu.addAction("重新下载")
        self.table_menu_action_stop_download = self.right_menu.addAction("停止下载")
        self.table_menu_action_del.triggered.connect(self.__delete_table_rows)

    # 显示表格右键菜单
    def __show_table_right_menu(self, point):
        # 使菜单在正常位置显示
        screen_pos = self.tableView.mapToGlobal(point)
        # 单击一个菜单项就返回，使之被阻塞
        self.right_menu.move(screen_pos)
        self.right_menu.show()

    # 删除表格数据
    def __delete_table_rows(self):
        indexes = self.tableView.selectionModel().selectedRows()
        if len(indexes) > 0:
            # 创建一个问答框，注意是Question
            box = QMessageBox(QMessageBox.Question, '删除行', '当前选中[' + str(len(indexes)) + ']条数据,确定删除吗?')
            # 添加按钮，可用中文
            yes = box.addButton('删除', QMessageBox.YesRole)
            cancel = box.addButton('取消', QMessageBox.RejectRole)
            # 设置消息框中内容前面的图标
            box.setWindowIcon(self.icon)
            # 显示该问答框
            box.exec_()

            # 判断分支选择
            if box.clickedButton() == yes:
                # 要删除的id集合
                del_id_list = []
                # 要删除的索引集合
                row_index_list = []
                # 先获取数据
                for i in indexes:
                    data_id = i.model().data(i)
                    del_id_list.append(data_id)
                    # 获取要删除行的索引
                    row_index_list.append(i.row())
                # 索引值倒序 从后往前删
                row_index_list.reverse()
                for index in row_index_list:
                    # 删除表格行
                    self.tableView.model.removeRow(index)
                # 同步删除数据
                for data_id in del_id_list:
                    for info in self.video_info_list:
                        # 根据id是否相等进行删除
                        if info['id'] == data_id:
                            self.video_info_list.remove(info)
                            break

    # 初始化配置文件
    def __init_config(self):
        self.conf = configparser.ConfigParser()
        # 读取文件
        self.conf.read("config.ini", encoding='utf-8')
        if os.path.lexists('config.ini'):
            self.conf_flag = True

    # 获取列表页
    def __get_list_info(self, text):
        self.__change_info_label('正在解析列表...')
        # 1.获取列表页
        try:
            html_info = self.http_client.get_html_format(text, timeout=10, is_proxies=True)
        except Exception as e:
            self.__change_info_label('解析失败!' + str(e))
            return
        self.__change_info_label('正在解析列表视频...')
        # 解析一页的信息
        item_info_div_list = html_info.find_all(
            attrs={'class': 'node node-video node-teaser node-teaser clearfix'})
        task_list = []
        # 获取
        for div_info in item_info_div_list:
            task_list.append(self.__parse_thread_pool.submit(self.__get_video_info, div_info))
        # 按顺序获取列表
        i = 0
        for task in task_list:
            i += 1
            try:
                # 获取解析信息
                video_info = task.result(timeout=10)
                # 设置发布顺序
                video_info.setdefault("release_order", str(i))
                # 放入集合
                self.video_info_list.append(video_info)
                # 更新数据表格
                self.__add_table_view_row(video_info)
                # 根据内容调整行高
                self.tableView.resizeRowsToContents()
            except Exception as e:
                self.__change_info_label("解析超时 跳过" + str(e))
        self.__change_info_label('解析地址完成')

    # 开启单个任务下载
    def __start_download(self):
        # 获取保存路径
        save_path = self.savePathEdit.text() + '/'
        if self.task_data.__len__() > 0:
            info = self.task_data.pop(0)
            # 实例化多线程对象
            thread = Worker(info=info, save_path=save_path, data_id=info['id'],
                            proxy_path=self.proxyPathEdit.text())
            # 信号与槽函数的连接
            thread.tableViewSign.connect(self.__update_table_item)
            thread.startSign.connect(self.__start_download)
            self.task_list.append(thread)
            thread.start()
        else:
            # 设置批量下载按钮可点击
            self.batchDownloadButton.setDisabled(False)

    # 解析视频信息
    def __get_video_info(self, div_info):
        # 解析视频哈希值
        video_hash = div_info.find('a')['href'][8:-17]
        # 解析作者
        username = div_info.find('a', attrs={'class': 'username'}).text
        # 解析视频标题
        video_title = div_info.find('img')['title']
        # 预览图片地址
        video_img_path = div_info.find('img')['src']
        # 解析like数
        video_like_num = div_info.find(attrs={'class': 'right-icon likes-icon'}).text.replace('\n', '').strip()
        # 解析观看数
        video_view_num = div_info.find(attrs={'class': 'left-icon likes-icon'}).text.replace('\n', '').strip()
        # 获取下载地址信息
        down_load_info = self.http_client.get_json('https://ecchi.iwara.tv/api/video/' + video_hash,
                                                   is_proxies=True)
        # 信息汇总
        video_info = {
            'id': str(uuid.uuid1()),
            'title': video_title,
            'like_num': video_like_num,
            'view_num': video_view_num,
            'img_path': 'https:' + video_img_path,
            'down_load_info': down_load_info,
            'uri': 'https:' + down_load_info[0]['uri'],
            'username': username
        }
        # 更新视图
        return video_info

    # ================================ 视图更新方法 =======================================
    # 更新表格接收信号方法
    def __update_table_item(self, args):
        process = QStandardItem(args[2])
        process.setTextAlignment(Qt.AlignCenter)
        size = QStandardItem(args[3])
        size.setTextAlignment(Qt.AlignCenter)
        # 设置搜索起始范围
        start = self.tableView.model.index(0, 0)
        # 查询对应单元格
        matches = self.tableView.model.match(start, Qt.DisplayRole, args[0], 1, Qt.MatchContains)
        # 找到匹配数据
        if matches:
            index = matches[0]
            # 行索引赋值
            self.tableView.model.setItem(index.row(), args[1], process)
            self.tableView.model.setItem(index.row(), args[1] + 1, size)

    # 表格添加行
    def __add_table_view_row(self, video_info):
        title = QStandardItem(video_info['title'])
        release_order = QStandardItem(video_info['release_order'])
        like_num = QStandardItem(video_info['like_num'])
        view_num = QStandardItem(video_info['view_num'])
        process = QStandardItem('0.000%')
        # 设置排序数据
        release_order.setData(int(video_info['release_order']), role=Qt.EditRole)
        like_num.setData(int(video_info['like_num']), role=Qt.EditRole)
        view_num.setData(float(video_info['view_num'].replace("k", "")), role=Qt.EditRole)
        # 设置data会覆盖原展示值 再次赋值
        view_num.setText(video_info['view_num'])

        title.setTextAlignment(Qt.AlignLeft | Qt.AlignBottom)
        release_order.setTextAlignment(Qt.AlignCenter)
        like_num.setTextAlignment(Qt.AlignCenter)
        view_num.setTextAlignment(Qt.AlignCenter)
        process.setTextAlignment(Qt.AlignCenter)

        # self.tableView.setIndexWidget()

        self.tableView.model.appendRow([
            QStandardItem(video_info['id']),
            title,
            release_order,
            like_num,
            view_num,
            process,
            QStandardItem('')
        ])

    # 下方信息展示
    def __change_info_label(self, info):
        self.infoLabel.setText(info)


# ================================ 程序入口 ================================
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main_form = MainForm()
    main_form.show()
    sys.exit(app.exec_())
