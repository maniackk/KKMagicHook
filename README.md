# KKMagicHook
[TimeProfiler](https://github.com/maniackk/TimeProfiler)的进阶库，可以可视化特定模块的OC方法耗时。

# 原理
通过静态库来静态插桩的方式，实现Hook拦截。

# 使用
hookObjcMsgSend.py脚本处理需要监控的静态库，将MagicHook文件夹拖入工程中。无需调用任何方法，App启动后，摇一摇就可以打开可视化OC耗时数据。

<div align="center"><img width="300" height="533.6" src="https://wukaikai.tech/images/tuchuang/talkingdata_haoshi.jpg"></div>


# 博客
[静态插桩的方式来实现Hook Method](https://juejin.im/post/5e74bc39f265da576a57a293)



