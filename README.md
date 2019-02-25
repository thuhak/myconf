# 通用配置文件类

## 功能

- 加载json或者yaml文件作为可嵌套的配置文件, 文件名必须以.json,.yaml或者是.yml结尾
- 支持子文件拆分，需要在json或者yaml中定义include这个key，值为子路径
- 配置实例的会随着配置文件的改变而变更,如果想禁用这个功能，需要可以传递参数refresh=False
- 支持在配置文件中注册多个回调函数，监控配置文件中的特定key，当key变化时，调用对应的回调函数进行处理

## 安装

```cmd
pip install myconf
```

## 使用举例

配置文件
```json
{
  "foo": {
      "bar": "abced"
  },
  "include": "/tmp/conf/"
}
```

### 一般情况

```python
from myconf import Conf
import time

config = Conf('/testconf/test.yml')

while True:
    print(config)
    time.sleep(1)

```

- 更改配置文件以后，config也会随着改变
- 需要注意mutable和imutable的区别。如果使用索引把config中的某个不可变类型(int, str等)的值赋予一个左值变量，那么这个变量是不会修改的.


### 使用回调

```python
from myconf import Conf
import logging

class MyConf(Conf):
    def onchange_a(self, old, new, watched_item='foo.bar'):
        logging.info('foo.bar changes from {} to {}'.format(old, new))

    def onchange_b(self, old, new, watched_item='a.b'):
        logging.info('a.b changes from {} to {}'.format(old, new))


config = MyConf('/testconf/test.yml')
```

1. 继承Conf类
2. 定义回调函数onchange_xx(self, old, new, watched_item="jmespath-expression")。
函数名称必须以onchange_开头，如果有多个回调函数，按照函数的名称排序依次执行。
函数中的old代表修改前的数据，new代表修改后的数据，这两个参数可以在函数中使用。
watched_item需要有一个jmespath表达式作为默认值，无需在函数中使用。
当配置中这个表达式搜索出的结果发生改变时，执行回调. jmespath表达式的使用可以参考[官方文档](http://jmespath.org)


## 注意事项

- 在处理子文件的时候，如果有重复的key，会依据加载顺序执行覆盖。为了避免不必要的麻烦，不要使用重复的key值
- 为了简便的实现快速加载，数据实际占用的存储空间会比原来翻倍
- Conf并没有实现__setitem__方法，相当于frozendict，但是加载进来的子项则是普通的dict。不要直接修改这些值，重新加载配置的时候会被刷新回来。
