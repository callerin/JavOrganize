import os
import time
import argparse
from organize_v import nfoTree
from concurrent.futures import ThreadPoolExecutor,as_completed

def process(file_src:str):
	# delete keywords
	del_key = ('107','002','229','230','263','287','298','355','406')
	file_name = os.path.split(file_src)[-1]

	data = nfoTree(file_src)
	node_t = data.root.find('title')
	node_s = data.root.find('sorttitle')
	num = data.num
	try:
		tittle= node_t.text
		sorttitle = node_s.text
		for arg in del_key:
			n = len(arg)
			if tittle.startswith(arg):
				node_t.text = tittle[n:]
				print(f'del {arg} {file_name} {num}')
			if sorttitle.startswith(arg):
				node_s.text = sorttitle[n:]
	except Exception as e:
		print(f'find tittle error\n{e}')

	data.tree.write(file_src,encoding='utf-8',xml_declaration=True)


def main():
	parser = argparse.ArgumentParser(description='Emby-generated NFO files.')
	parser.add_argument('-o', '--src_dir',type=str,default='./',help='Source directory containing NFO and Movie files.')

	args = parser.parse_args()
	src_dir = os.path.abspath(args.src_dir)

	nfo_list = []

	print('getting nfo files')
	begin = time.time()
	for root, dirs, files in os.walk(src_dir):
		for file in files:
			if file.endswith('.nfo'):
				file_src = os.path.join(root, file)
				nfo_list.append(file_src)

	stop = time.time()
	print(f'getting nfo files ready. time:{stop-begin}')

	max_worker = 8

	with ThreadPoolExecutor(max_worker) as pool:
		[pool.submit(process,nfo) for nfo in nfo_list]

if __name__ == '__main__':
	main()
