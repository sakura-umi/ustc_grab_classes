# ustc 选课/监控脚本

ustc选课/监控脚本+bot推送

## 请不要滥用！脚本开发者不对一切滥用导致的后果负任何责任！  

### 功能

- 20210907：创建脚本，支持选课或监控课程人数变化并提醒
- 20210908：支持输入课程名称和老师，修正bugs。
- 20210909：将选课/监控作为一个脚本的两个模式，并作为输入参数合并到一个脚本中，原监控脚本弃置。
- 20210910：支持同类课程不同老师之间换班选课，支持输入课程名称和老师等信息自动检索课程，支持`go-cqhttp`类qqbot接口推送，修复bugs。
- 20210918：优化qqbot推送信息显示，优化参数输入模式和命令行显示，引入`argparse`，增加`查询间隔`参数。
- 20220110：一次计算当前学期的id值尝试(现确认失败)
- 20220324：支持选择不同学期，适配选课新界面，修复bugs。

### 用法

`python3 grabbing.py [-h] [-m MODE] [-c CLASSTYPE] [-t TIME] name teacher qqnum [classid]`

1. 将脚本内的账号, 密码, qq号, boturl等参数填好
2. 安装依赖
3. 运行脚本
4. 各项参数具体作用如下, -h也会输出

```none
positional arguments:
  name                  选中课程的中文名称
  teacher               选中课程的授课老师
  qqnum                 你要私聊提醒的qq号
  classid               课程号, 若前两项已经可以唯一确定则可以为空(如果不唯一的话, 不要为空!)

optional arguments:
  -h, --help            show this help message and exit
  -m MODE, --mode MODE  模式选择, grab为抢课模式, monitor为监控模式, 默认为监控模式.
  -c CLASSTYPE, --classtype CLASSTYPE
                        课程类别选择, public为公选课, major为专业课, 默认为公选课模式. 区别为专业课可以个性化申请，公选课不允许个性化申请.
                        如果想即选即中请选择public.
  -t TIME, --time TIME  两次查询间隔时间，单位为秒 (默认为60).
```

### 欢迎上报bug或pr