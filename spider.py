#coding=utf-8
from bs4 import BeautifulSoup
from BloomFilter import BloomFilter
from Queue import Queue
from urlparse import *     #根据url提取域名的函数
from threading import Thread,Lock,local
import urllib2
import sys

#将起始url放入队列和BloomFilter中
def init(domain):
	urls.put('http://'+domain)  #put是Queue的方法，在urls队尾插入一个项目 
	bf.insert('http://'+domain)

class spider_thread(Thread):
	def __init__(self,thread_id):
		super(spider_thread,self).__init__()  #super语句保证公共父类只被调用一次
		self.thread_id = thread_id
	def run(self):
		spider()

def spider():
	while not urls.empty():   #urls.empty()队列为空返回True，此语句判断urls是否非空，非空则继续执行
		threadlock.acquire()
		now = urls.get()   #调用队列对象的get()方法从队头删除并返回一个项目
		threadlock.release()  #保证只有一个线程能访问共享资源
		print now
		try:
			#伪造浏览器头，防止反爬虫
			req = urllib2.Request(now)  #向服务器提出请求
			req.add_header('User-Agent','Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0')
			res = urllib2.urlopen(req)
			now=res.geturl().strip('/')   #删除两边的'/'符号
			#规范化url，获得当前目录
			now_path = urlsplit(now).path.split('.')  #把path和params分开（urlsplit),再通过split把地址字符串和'html'分开
			if len(now_path)>1:  #如果有'html'
				tmp = now.split('/')
				now = '/'.join(tmp[:-1])  #把最后一个字符串'html'去掉，其余用'/'连接
			#用BeautifulSoup分析页面
			soup = BeautifulSoup(res.read(),"html.parser")  #用BeautifulSoup返回格式化的网页内容
		except:
			continue
		for a in soup.find_all('a'):  #找出页面中的所有超链接
			try:
				#统一编码
				href = a['href'].encode('utf-8').strip('/')
				if href.startswith('javascript'):
					continue
				#将采用相对目录的url规范化
				if not href.startswith('http'):
					href = now + '/' + href.lstrip('.').lstrip('/')
				parts = urlsplit(href)
				path=parts.path.split('.')
				#只分析特定格式的页面
				if len(path)>1 and path[1] not in suffix:
					continue
				if parts.netloc == domain:
					#分解url判重
					q = parts.query.split('&')
					if q[0] != '':
						for i in range(len(q)):
							tmp = q[i].split('=')
							#只有请求参数值不同，且参数值为数字的url只分析一次
							if tmp[1].isdigit():
								q[i] = tmp[0]+'='
					new_query='&'.join(q)
					new_href = urlunsplit((parts.scheme,parts.netloc,parts.path,new_query,parts.fragment))
					#beautifulsoup中没有该类url则加入队列
					if not bf.isContain(new_href):
						threadlock.acquire()
						bf.insert(new_href)
						urls.put(href)
						threadlock.release()
			except:
				pass
if __name__ == '__main__':    #命令行直接运行时启动，在python中import时不启动
	suffix=['aspx','jsp','php','html','htm']
	urls = Queue()
	
	#高效判重数据结构
	bf = BloomFilter()
	domain = sys.argv[1]   #把命令行第二个字符串赋值给domain

	#获取参数
	num_thread = int(sys.argv[2])
	init(domain)

	#多线程
	threads = []
	threadlock = Lock()
	data = local()   #保存全局变量data（在每个线程中有副本）
	for i in range(num_thread):
		mythread = spider_thread(i)
		threads.append(mythread)
	for i in range(num_thread):
		threads[i].start()  #进程p调用start()时，自动调用run()
	for i in range(num_thread):
		threads[i].join()    #调用Thread.join将会使主调线程堵塞，直到被调用线程运行结束或超时
	
