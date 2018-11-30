# 通用配置文件类

## 功能

- 加载json或者yaml文件作为可嵌套的配置文件
- 支持子文件拆分，需要在json或者yaml中定义include这个key，值为子路径
- 在有inotify的情况下，支持根据配置文件动态变更

## 举个栗子

```python
from myconf import Conf
import time

config = Conf('/etc/config.json')

while True:
    print(config)
    time.sleep(1)

```

配置文件
```json
{
  "arg1": "g",
  "arg2": ["d","e","g"],
  "include": "/tmp/conf/"
}
```


## 注意事项

在处理子配置文件的时候，如果有重复的key值，会不断覆盖之前的对应key的value.
为了避免混乱，请不要使用重复的key值
