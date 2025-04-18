import os
import argparse
import yaml
import jmcomic
import jmcomic.jm_exception
from PIL import Image
from reportlab.pdfgen import canvas


def main():
    # 自定义设置：
    config = "config.yml"
    option = jmcomic.create_option_by_file(config)
    with open(config, "r", encoding="utf8") as f:
        path = yaml.load(f, Loader=yaml.FullLoader)["dir_rule"]["base_dir"]
    
    for ID in download_list:
        album = [file for file in os.listdir(path) if file.endswith("(JM{}).pdf".format(ID))]
        if album:
            print("{} 已存在".format(album[0]))
            continue
        
        file = os.path.join(path, ID)
        if not os.path.exists(file):
            print("准备下载 JM{}".format(ID))
            try:
                album = jmcomic.download_album(ID, option)[0]
            except jmcomic.jm_exception.RequestRetryAllFailException:
                # 目前存在缺陷, 只能捕获第一次网络异常
                # 由于后续下载分在不同线程中, 因此这些异常不能被主线程捕获
                # 我不想使用 sys.excepthook 全局捕获, 所以暂时没办法
                print("下载 JM{} 失败, 可能是网络原因".format(ID))
                continue
        
        # 按章节排列顺序
        file = next(os.scandir(file))
        episode = []  # 章节目录(标准名称为photo)
        with os.scandir(file) as entries:
            for entry in entries:
                if entry.is_dir():
                    episode.append(entry.name)
        episode.sort(key=int)  # 按数字大小进行排序
        
        # 创建PDF流
        print("正在将《{}》转换为PDF".format(file.name))
        c = canvas.Canvas(os.path.join(path, file.name) + " (JM{}).pdf".format(ID))
        for i in range(len(episode)):
            images = []  # 章节内图片索引(仅含文件名)
            with os.scandir(os.path.join(file, episode[i])) as entries:
                for entry in entries:
                    images.append(entry.name)
            images.sort()
            print("第{}话 共{}页".format(episode[i], len(images)))
            
            for image in images:
                image = os.path.join(file, episode[i], image)
                c.setPageSize(Image.open(image).size)
                c.drawImage(image, x=0, y=0)
                c.showPage()  # 结束当前页
        c.save()
        
        print("《{}》转换完成".format(file.name))


if __name__ == '__main__':
    download_list: list[str] = ['']
    parser = argparse.ArgumentParser()
    parser.add_argument('--add', nargs='+', default=[], help='输入JM编号')
    download_list.extend(parser.parse_args().add)
    main()

