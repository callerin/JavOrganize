import re
import os
import sys
import logging
import argparse
from unittest import result
import xml.etree.ElementTree as ET
from shutil import move
from send2trash import send2trash

# logging.disable(logging.INFO)
# logging.disable(logging.DEBUG)
logging.basicConfig(level=logging.INFO,
					format=" %(asctime)s - %(levelname)s - %(message)s")


class nfoTree:

	def __init__(self, nfo_file):
		self.tree = ET.parse(nfo_file)
		self.root = self.tree.getroot()
		self.num = self.get_num()
		self.actor = self.get_actor()
		self.title = self.get_title()
		self.stitle = self.get_title('title')
		self.nfo_name = self.get_nfo(nfo_file)
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
					# 控制获得果实，或者枝头的其他属性
					if child.text is None:
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
			print(f'{self.num} actor is null')

	def get_title(self, stag='originaltitle'):
		title_node = self.root.findall(stag)
		try:
			title = title_node[0].text
			return title
		except Exception as e:
			logging.error(f'Get title error{e}')

	def get_num(self):

		title_node = self.root.findall('title')
		try:
			title = title_node[0].text
		except Exception as e:
			logging.error(f'Get stitle error{e}')

		expr = r'(\d\d\d)?[a-zA-Z]{0,8}\d{0,5}-\d{1,7}'
		exp = re.compile(expr)
		try:
			num = exp.search(title).group()  # type: ignore
		except Exception as e:
			num = None
			logging.error(f'{title} get num wrong {e}')
		return num

	def get_apple(self):
		# 得到所有水果
		self.grow_apple(self.root)
		return self.apple

	def get_nfo(self, name):
		nfo_name = os.path.split(name)

		return nfo_name[1]


class movie:

	def __init__(self, f_name: dict):
		self.nfo = nfoTree(f_name['fname'])
		self.name = self.get_name(f_name)
		self.files = self.get_file(f_name)
		self.status = self.check(del_file=True)
		self.num = self.nfo.num
		self.type = self.get_type()

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
			logging.error(f'Get file error{e}')

		return flist

	def get_name(self, file_name):
		name = os.path.splitext(file_name['name'])[0]
		if 'cd1' in name or 'CD1' in name:
			name = name.replace('CD1', 'cd1')
			name = name.replace('.cd', '-cd')
			tmp = name.split('-cd1')
			name = tmp[0]

		str_keep = ('-4k.', '-1080p.', '-C.')
		for arg in str_keep:
			name = name.replace(arg, '')
		return name

	def check(self, del_file):
		# 判断是否缺少视频文件
		file_end = ('.mp4', '.wmv', '.mov', '.mkv', 'avi', 'iso','.MP4')
		count = 0

		for file in self.files:
			if file['name'].endswith(file_end):
				count = count + 1

		if del_file and count == 0:
			for file in self.files:
				send2trash(file['fname'])
				name = file['name']
				logging.info(f'{name} is send2trash')

		return count

	def get_type(self):
		tag = []
		str_keep = ('-4k', '-1080p', '-C', '-4K')
		name = self.name
		for arg in str_keep:
			if arg in name:
				tag.append(arg)
				break
		return tag


def norm_name(fnam: str):
	if fnam is None or not isinstance(fnam, str):
		return None

	ch_forbid = (':', '/', '\\', '?', '*', '|', '<', '>', '！','+')
	ch_replace = ' '
	max_len = 60  # windows max 250

	new_name = fnam
	for ch in ch_forbid:
		new_name = new_name.replace(ch, ch_replace)
	if len(new_name) > max_len:
		new_name = new_name[0:max_len]
		logging.warning(f'file name is been cut:{new_name}')

	return new_name


def rename_single_dir(file_path: str, str_ig):
	# 单独文件夹影片重命名，适配 organiz_file()函数识别影片文件
	if not os.path.exists(file_path):
		logging.error(f'dir {file_path} not exist')
		return False

	file_end = ('.mp4', '.wmv', '.mov', '.mkv', '.avi',
				'.jpg', '.png', '.ass', '.srt', '.sub')

	flag_nfo = True
	name_movie = ''
	for root, dirs, files in os.walk(file_path):
		nfo_list = []
		temp_nfo = {}
		for file in files:
			if file.endswith('.nfo'):
				name_movie = os.path.splitext(file)[0]
				if '-cd' in name_movie or '-CD' in name_movie:
					name_movie = name_movie[0:-4]
				for arg in str_ig:
					name_movie = name_movie.replace(arg, '')
				flag_nfo = False

				temp_nfo = {}
				file_src = os.path.join(root, file)
				temp_nfo['name'] = file
				temp_nfo['path'] = root
				temp_nfo['fname'] = file_src
				nfo_list.append(temp_nfo)

		if flag_nfo:
			continue
		if len(nfo_list) != 1:
			continue
		temp_movie = movie(nfo_list[0])
		if temp_movie.status != 1:
			continue

		for file in files:
			temp1 = file.upper()
			temp2 = name_movie.upper()
			if not temp2 in temp1:
				if file == 'log.txt':
					continue
				if not any(file.endswith(arg) for arg in file_end):
					continue

				fname = os.path.join(root, file)
				temp = temp_movie.name + '-' + file  # type: ignore
				new_name = os.path.join(root, temp)
				try:
					os.rename(fname, new_name)
					logging.info(f'{file} is renamed to {temp}')
				except Exception as e:
					logging.error(f'{file} renamed error {e}')


def remove_null_dirs(origin_dir: str) -> list:
	"""
	删除空文件夹
	Args:
			origin_dir:

	Returns:

	"""
	file_remove = []

	del_keys = ('.TXT','.txt','.url')
	# topdown=False 递归文件夹深度 由下到上
	for root, dirs, files in os.walk(origin_dir, topdown=False):
		for file in files:
			if any(arg in file for arg in del_keys):
				try:
					send2trash(file)
					file_remove.append(file)
				except Exception as e:
						logging.info(e)

		for dir1 in dirs:
			dir_path = os.path.join(root, dir1)
			allfiles = os.listdir(dir_path)
			if len(allfiles) == 0:
				# os.removedirs(dir_path)
				send2trash(dir_path)
				file_remove.append('.\\' + dir_path.split('\\')
								   [-2] + '\\' + dir_path.split('\\')[-1])
	# file_remove.append(dir_path.split('\\')[-1])
	return file_remove


def organiz_file(origin: str, destination: str, hardlink: bool):
	count = {'file': 0, 'movie': 0}
	if not os.path.exists(origin):
		logging.error(f'dir {origin} not exist')
		return count

	nfo_list = []
	movies = []

	str_keep = ('-4k', '-1080p', '-C', '-4K')
	rename_single_dir(origin, str_keep)

	for root, dirs, files in os.walk(origin):
		for file in files:
			if file.endswith('.nfo'):
				temp = {}
				file_src = os.path.join(root, file)
				temp['name'] = file
				temp['path'] = root
				temp['fname'] = file_src
				nfo_list.append(temp)

	for nfo in nfo_list:
		try:
			temp = movie(nfo)
		except Exception as e:
			logging.error(f'get movie nfo wrong {nfo}')
		if temp.status:
			movies.append(temp)

	if len(movies) == 0:
		return count

	for data in movies:
		name = data.name
		files = data.files
		actor = data.nfo.actor
		num_m = data.nfo.num
		title = data.nfo.title

		str_ignore = ()

		if any(arg in name for arg in str_ignore):
			logging.info(f'{name} ignored')
			continue

		if title is None:
			logging.warning(f'{name} missing title')
			continue

		if num_m is None:
			logging.warning(f'{name} missing num')
			continue

		if actor is None:
			logging.warning(f'{name} missing actor')
			new_name = num_m + ' ' + title
			actor = 'NULL'
		elif actor in title:
			new_name = num_m + ' ' + title
		else:
			new_name = num_m + ' ' + title + actor

		tag = data.type
		if tag:
			new_name += tag[0]

		new_name = norm_name(new_name)
		if data.status > 1:
			new_name = num_m

		full_name = files[0]['fname']
		if 'cd' in full_name or 'CD' in full_name or data.status > 1:
			tmp = os.path.join(destination, actor)
			path_actor = os.path.join(tmp, num_m)
		else:
			path_actor = os.path.join(destination, actor)

		# makedir with actor name
		if not os.path.exists(path_actor):
			os.makedirs(path_actor)
			logging.info(f'mkdir {actor}')

		# skip aria2 downloading file
		for file in files:
			sname = file['name']
			if sname.endswith('.aria2'):
				print(f'skip {sname}')
				continue

		for file in files:
			fname = file['fname']
			sname = file['name']
			dfile = sname.replace(name, new_name)
			dest_file = os.path.join(path_actor, dfile)
			try:
				if fname == dest_file:
					continue

				if hardlink and sname.endswith(('mp4','mkv','avi')):
					os.link(fname, dest_file)
				else:
					move(fname, dest_file)

				logging.info(f'{sname} is moved to {actor}')
				logging.info(f'Renamed to {dfile}')
				count['file'] += 1
			except Exception as e:
				logging.error(f'Move file error{e}')

		count['movie'] += 1

	return count


def main():
	parser = argparse.ArgumentParser(
		description='Organize video files based on Emby-generated NFO files.')
	parser.add_argument('-o', '--src_dir', type=str, default='./', help='Source directory containing NFO and Movie files.')
	parser.add_argument('-d', '--dest_dir', type=str, default='./',	help='Destination directory where the organized files will be stored.')
	parser.add_argument('-l', '--hardlink', type=bool, default=False, help='Do not move media file, Create hardlink.')

	args = parser.parse_args()

	src_dir = os.path.abspath(args.src_dir)
	dest_dir = os.path.abspath(args.dest_dir)
	hardlink = args.hardlink

	if not os.path.exists(src_dir):
		print('Source directory does not exist.')
		sys.exit(1)

	count = organiz_file(src_dir, dest_dir, hardlink)
	remove = remove_null_dirs(src_dir)
	print(f'{remove} is send2transh')
	print(count)
	logging.info('Complet:{}'.format(count['movie']))


if __name__ == '__main__':
	main()
