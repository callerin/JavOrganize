
import re
import os
import logging
import xml.etree.ElementTree as ET
from shutil import move
from send2trash import send2trash

# logging.disable(logging.INFO)
# logging.disable(logging.DEBUG)
logging.basicConfig(filename='log.txt', level=logging.DEBUG,
                    format=" %(asctime)s - %(levelname)s - %(message)s")


class nfoTree:
	def __init__(self, nfo_file):
		self.tree = ET.parse(nfo_file)
		self.root = self.tree.getroot()
		self.num = self.get_num()
		self.actor = self.get_actor()
		self.title = self.get_title()
		self.stitle = self.get_title('title')
		self.apple = []
		logging.debug(f'Get {self.num}')

	def val_leaves(self, node):
		# 判断是否为叶子节点
		children = []
		for child in node:
			children.append(child)
		if len(children) == 0:
			return True
		else:
			return False

	def get_children(self, node):
		# 产生儿子节点
		children = []
		for child in node:
			children.append(child)
		return children

	def grow_apple(self, node):
		# 长出水果
		if self.val_leaves(node):
			pass
		else:
			children = self.get_children(node)
			basket = []
			for child in children:
				if self.val_leaves(child):
					# 控制得到是果实，或者枝头的其他属性
					if child.text == None:
						basket.append(child.attrib)
					else:
						basket.append(child.text)
				else:
					self.grow_apple(child)
			self.apple.append(basket)

	def get_actor(self):
		actor_name = []
		actor_node = self.root.findall('actor')
		try:
			name = actor_node[0].find('name')
			actor_name = name.text
			return actor_name
		except Exception as e:
			logging.error(f'{self.num} actor is null')

	def get_title(self, stag='originaltitle'):
		title_node = self.root.findall(stag)
		try:
			title = title_node[0].text
			return title
		except Exception as e:
			logging.error(e)

	def get_num(self):

		title_node = self.root.findall('title')
		try:
			title = title_node[0].text
		except Exception as e:
			logging.error(e)

		expr = r'(\d\d\d)?[a-zA-Z]{0,8}\d{0,5}-\d{1,3}'
		exp = re.compile(expr)
		try:
			num = exp.search(title).group()
		except Exception as e:
			num = None
			logging.error(f'{title} get num wrong {e}')
		return num

	def get_apple(self):
		# 得到所有水果
		self.grow_apple(self.root)
		return self.apple


class movie:
	def __init__(self, f_name: dict):
		self.nfo = nfoTree(f_name['fname'])
		self.name = self.get_name(f_name)
		self.files = self.get_file(f_name)
		self.status = self.check(del_file=True)

	def get_file(self, file):
		flist = []
		try:
			path = file['path']
			name = self.name
			for root, dirs, files in os.walk(path):
				for file in files:
					if name in file:
						temp = {}
						file_src = os.path.join(root, file)
						temp['name'] = file
						temp['fname'] = file_src
						flist.append(temp)

		except Exception as e:
			logging.error(e)
		return flist

	def get_name(self, file_name):
		name = os.path.splitext(file_name['name'])[0]
		return name

	def check(self, del_file):
		# 判断是否缺少视频文件，
		file_end = ('.mp4', '.wmv', '.mov', '.mkv', 'avi')
		flag = False

		for file in self.files:
			if file['name'].endswith(file_end):
				flag = True
				break

		if del_file and not flag:
			for file in self.files:
				send2trash(file['fname'])
				name = file['name']
				logging.info(f'{name} is send2trash')

		return flag


def organiz_file(origin: str, destination: str):

	nfo_list = []
	movies = []

	for root, dirs, files in os.walk(origin):
		for file in files:
			if file.endswith('nfo'):
				temp = {}
				file_src = os.path.join(root, file)
				temp['name'] = file
				temp['path'] = root
				temp['fname'] = file_src
				nfo_list.append(temp)

	for nfo in nfo_list:
		temp = movie(nfo)
		if temp.status:
			movies.append(temp)

	for data in movies:
		name = data.name
		files = data.files
		actor = data.nfo.actor
		num_m = data.nfo.num
		title = data.nfo.title

		str_ignore = ('FC2', 'fc2')

		if any(arg in name for arg in str_ignore):
			logging.info(f'{name} ignored')
			continue

		if actor is None:
			logging.warning(f'{name} missing actor')
			continue

		if actor in title:
			new_name = num_m + ' ' + title
		else:
			new_name = num_m + ' ' + title + actor

		path_actor = os.path.join(destination, actor)
		# makedir with actor name
		if not os.path.exists(path_actor):
			os.mkdir(path_actor)
			logging.info(f'mkdir {actor}')

		for file in files:
			fname = file['fname']
			sname = file['name']
			dfile = sname.replace(name, new_name)
			dest_file = os.path.join(path_actor, dfile)
			try:
				move(fname, dest_file)
				logging.info(f'{sname} is moved to {actor}')
			except Exception as e:
				logging.error(e)

	return nfo_list


if __name__ == '__main__':
	file_path = r'D:\Download\QQDownload\Single'  # 待处理文件目录
	file_dest = r'D:\Download\QQDownload\Named'	  # 移动文件目标位置

	organiz_file(file_path, file_dest)
