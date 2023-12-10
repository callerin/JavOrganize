import re
import os
import sys
import logging
import argparse
import time
from unittest import result
import xml.etree.ElementTree as ET
from shutil import move
from send2trash import send2trash
from concurrent.futures import ThreadPoolExecutor,as_completed

# logging.disable(logging.INFO)
# logging.disable(logging.DEBUG)
logging.basicConfig(level=logging.INFO,filename="log.txt",filemode="a",
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

	def get_title(self, stag='originaltitle'):
		title_node = self.root.findall(stag)
		try:
			title = title_node[0].text
			return title
		except Exception as e:
			logging.error(f'Get title error{e}')

	def get_num(self):
		del_key = ('107','002')

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

		for tag in del_key:
			if num.startswith(tag):
				n = len(tag)
				num=num[n:]
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
		#  0  	无视频文件
		#  1  	1个文件
		# -1 	缺少图片文件
		file_end = ('.mp4', '.wmv', '.mov', '.mkv', 'avi', 'iso')
		file_image = ('.png','.jpg')
		count_media = 0
		count_image = 0

		for file in self.files:
			temp = file['name'].lower()
			if temp.endswith(file_end):
				count_media = count_media + 1
			elif temp.endswith(file_image):
				count_image = count_image + 1

		if del_file and count_media == 0:
			for file in self.files:
				send2trash(file['fname'])
				name = file['name']
				logging.info(f'{name} is send2trash')

		if count_image == 0:
			file_temp = self.files[0]
			file_temp = file_temp['name']
			logging.warning(f'missing image file\n{file_temp}')
			#print(file_temp)
			return -1

		return count_media

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
	max_len = 80  # windows max 250

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
	file_end = ('.mp4', '.wmv', '.mov', '.mkv', 'avi', 'iso')
	file_image = ('fanart','landscape','poster')
	del_keys = ('强 力 推 荐','高速連接')

	flag_nfo = True
	name_movie = ''
	for root, dirs, files in os.walk(file_path):
		nfo_list = []
		temp_nfo = {}
		file_list = []
		image_list = []
		movie_list = []

		for file in files:
			# delete files
			if any(arg in file for arg in del_keys):
				try:
					send2trash(os.path.join(root,file))
					logging.info(f'{file} deleted')
					if file.endswith(file_end):
						print(f'{file} deleted')
				except Exception as e:
					logging.error(f'delete file error\n{e}')

			# rename series movie with cd1 cd2 ...
			result = rename_file(root,file)
			new_name = os.path.split(result)[-1]
			file_list.append(new_name)
			if new_name.endswith('.nfo'):
				nfo_list.append(new_name)
			elif file.startswith(file_image):
				image_list.append(new_name)
			elif new_name.endswith(file_end):
				movie_list.append(new_name)
			elif new_name.endswith('.nfo'):
				nfo_list.append(new_name)

		flag_re = True

		if len(movie_list)<1:
			continue
		m1 = movie_list[0]
		name_movie = os.path.splitext(m1)[0]
		name_s = name_movie.replace('-CD','-cd')
		name_s = name_s.split('-cd')[0]

		#if len(movie_list)==1 and len(nfo_list)==1:
		if len(movie_list)==1 :
			flag_re = True
		elif len(movie_list)>1:
			for movie in movie_list:
				if not movie.startswith(name_s):
					flag_re = False
					break
		else:
			flag_re = False

		if flag_re:
			for image in image_list:
				if len(movie_list) > 1:
					new_name = name_s + '-cd1-' + image
				else:
					new_name = name_s + '-' + image

				temp1 = os.path.join(root,image)
				temp2 = os.path.join(root,new_name)
				try:
					os.rename(temp1, temp2)
				except Exception as e:
					logging.error(f'{temp1} renamed error\n{e}')


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
			if file.startswith('log'):
				continue
			if any(arg in file for arg in del_keys):
				try:
					full_name = os.path.join(root,file)
					send2trash(full_name)
					file_remove.append(file)
				except Exception as e:
						logging.info(e)

		for dir1 in dirs:
			dir_path = os.path.join(root, dir1)
			allfiles = os.listdir(dir_path)
			if len(allfiles) == 0:
				# os.removedirs(dir_path)
				send2trash(dir_path)
				try:
					temp = os.path.split(dir_path)[-1]
					file_remove.append('.\\' + temp)
				except Exception as e:
					logging.error(f'remove error\n{e}')
	# file_remove.append(dir_path.split('\\')[-1])
	return file_remove


def rename_file(file_path:str,file_name:str) -> str:
	"""
	重命名文件	仅处理单独文件夹内的文件
	:param file_path: 文件绝对路径
	:return:

	"""
	pattern1 = ['_', '-']
	pattern2 = ['1', '2', '3', '4',
             'A', 'B', 'C', 'D', 'E', 'a', 'b', 'c', 'd', 'e'
				]
	pattern3 = ['.', '-']
	number = {
		'A': '1',
		'B': '2',
		'C': '3',
		'D': '4',
		'E': '5',
		'a': '1',
		'b': '2',
		'c': '3',
		'd': '4',
		'e': '5',
	}

	result = os.path.join(file_path,file_name)
	file = result
	file_sname = os.path.splitext(file_name)[0]
	for pat1 in pattern1:
		for pat2 in pattern2:
			for pat3 in pattern3:
				pattern = pat1 + pat2 + pat3
				if pattern in file_name:
					series = '-cd' + pat2 + pat3
					result = file_name.replace(pattern, series)
					if pat2 in number:
						result = result.replace(pat2, number[pat2])

					temp = file_name.split(pattern)
					temp_name = temp[0]
					des_path = os.path.join(file_path, temp_name)

					if not os.path.exists(des_path):
						os.mkdir(des_path)

					des = os.path.join(des_path, result)
					if not os.path.exists(des):
						move(file, des)
					# print("{} renamed {}".format(file.split('\\')[-1], result.split('\\')[-1]))
					break
	return result

def main_process(nfo:dict,key_list:list):
	move_file=0
	move_movie=0
	try:
		f_name = nfo['fname']
		movie_c = movie(nfo)
		if movie_c.status == 0:
			return [0,0]
	except Exception as e:
		print(f'get movie nfoTree wrong {f_name}')
		logging.error(f'get movie nfoTree wrong {f_name}\n{e}')
		return [0,0]

	move_file=0
	move_movie=0
	origin = key_list[0]
	destination = key_list[1]
	hardlink = key_list[2]
	miss = key_list[3]
	miss_folder = os.path.join(destination, 'miss_file')

	name = movie_c.name
	files = movie_c.files
	actor = movie_c.nfo.actor
	num_m = movie_c.nfo.num
	tittle = movie_c.nfo.title
	full_name = files[0]['fname']

	str_ignore = ()

	if any(arg in name for arg in str_ignore):
		logging.info(f'{name} ignored')
		return [0,0]

	if tittle is None:
		logging.warning(f'{name} missing title')
		return [0,0]

	if num_m is None:
		logging.warning(f'{name} missing num')
		return [0,0]

	tittle = norm_name(tittle)

	if actor is None:
		logging.warning(f'{full_name} missing actor')
		new_name = num_m + ' ' + tittle
		actor = 'NULL'
	elif actor in tittle:
		new_name = num_m + ' ' + tittle
	else:
		new_name = num_m + ' ' + tittle + actor

	tag = movie_c.type
	if tag:
		new_name += tag[0]

	if movie_c.status > 1:
		new_name = num_m

	# move missing image media to other folder
	if movie_c.status == -1 and miss:
		destination = miss_folder
		logging.warning(f'miss image {tittle}')

		for file in files:
			fname = file['fname']
			sname = file['name']
			dest = os.path.join(destination,sname)
			if not os.path.exists(destination):
				os.makedirs(destination)
			try:
				move(fname,dest)
				print(f'move miss file\n{sname}')
			except Exception as e:
				logging.error(f'move miss file error{e}')
			continue

	if 'cd' in full_name or 'CD' in full_name or movie_c.status > 1:
		tmp = os.path.join(destination, actor)
		path_actor = os.path.join(tmp, num_m)
	else:
		path_actor = os.path.join(destination, actor)

	# makedir with actor name
	if not os.path.exists(path_actor):
		try:
			os.makedirs(path_actor)
			logging.info(f'mkdir {actor}')
		except Exception as e:
			logging.error(f'make actor dir error{e}')

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
				logging.info(f'{sname} is linked to {dfile}')
			else:
				if os.path.exists(dest_file):
					print(f'{dfile} exists')
					logging.warning(f'{fname} {dest_file} exists')
					continue
				move(fname, dest_file)
				logging.info(f'{sname} is moved to {actor} {dfile}')

			logging.info(f'Renamed {sname} to {dfile}')
			move_file += 1
			if sname.endswith(('mp4','mkv','avi')):
				print(f'actor:{actor}\n{sname}  rename\n{dfile}\n')

		except Exception as e:
			logging.error(f'Move file error{e}')

	move_movie += 1

	return [move_file,move_movie]


def organiz_file(origin: str, destination: str, hardlink: bool, miss:bool):
	count = {'file': 0, 'movie': 0}
	if not os.path.exists(origin):
		logging.error(f'dir {origin} not exist')
		return count
	miss_folder = os.path.join(origin,'miss_file')

	nfo_list = []
	movies = []

	str_keep = ('-4k', '-1080p', '-C', '-4K')
	rename_single_dir(origin, str_keep)

	print('getting nfo files')
	begin = time.time()
	for root, dirs, files in os.walk(origin):
		for file in files:
			if file.endswith('.nfo'):
				expr = r'cd(\d){1}'
				exp = re.compile(expr,re.IGNORECASE)
				cds = exp.findall(file)
				if len(cds):
					if cds[0] != '1':
						continue

				temp = {}
				file_src = os.path.join(root, file)
				temp['name'] = file
				temp['path'] = root
				temp['fname'] = file_src
				nfo_list.append(temp)
	stop = time.time()
	print(f'getting nfo files ready. \ntime:{stop-begin}')

	max_worker = 8

	with ThreadPoolExecutor(max_worker) as pool:
		keys = [origin,destination,hardlink,miss]
		futures = [pool.submit(main_process,nfo,keys) for nfo in nfo_list]
		pool.shutdown(wait=True)
		for fut in as_completed(futures):
			data = fut.result()
			if not data is None:
				count['file'] += data[0]
				count['movie'] += data[1]

	return count


def main():
	parser = argparse.ArgumentParser(
		description='Organize video files based on Emby-generated NFO files.')
	parser.add_argument('-o', '--src_dir', type=str, default='./', help='Source directory containing NFO and Movie files.')
	parser.add_argument('-d', '--dest_dir', type=str, default='./',	help='Destination directory where the organized files will be stored.')
	parser.add_argument('-l', '--hlink', type=int, default=0, help='Do not move media file, Create hardlink.')
	parser.add_argument('-m', '--m_image', type=int, default=0, help='move files whithout images to other folder.')

	args = parser.parse_args()

	src_dir = os.path.abspath(args.src_dir)
	dest_dir = os.path.abspath(args.dest_dir)

	if args.hlink>0:
		hardlink = True
	else:
		hardlink = False

	if args.m_image>0:
		miss = True
	else:
		miss = False

	if not os.path.exists(src_dir):
		print('Source directory does not exist.')
		sys.exit(1)

	begin = time.time()
	count = organiz_file(src_dir, dest_dir, hardlink, miss)
	remove = remove_null_dirs(src_dir)
	print(f'{remove} is send2transh')
	print(count)
	logging.info('Complet:{}'.format(count['movie']))
	stop = time.time()
	logging.info(f'time:{stop - begin}')
	print(f'time:{stop - begin}')

if __name__ == '__main__':
	main()
