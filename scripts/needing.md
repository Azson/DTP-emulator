##需求

- 写一个脚本：
  - 不断调整网络状态，产生100种随机的网络
  - 在每种网络状态下分别运行这两种算法，将产生的QOE保存起来并画图进行对比
 
- 在新的qoe计算公式下，对比两种算法的表现：
  - 新的qoe1 = 1 * block_a + 1 * block_b + 1 * block_c
  - 新的qoe2 = sum((block_finish_time - block.timestamp) / block.deadline) 
   (qoe越大的话表现的反而不好)
  - 将产生的结果差距大的一组情况的trace 和 qoe 的 log 保存起来。
  
## 结果
- 结果1： 
  - 第一个qoe的计算公式下，基于deadline的方法表现要比基于优先级的表现好
  （都无法达到满的qoe的情况下），
  - 第二个qoe的计算公式下，基于deadline的方法（石老板）产生的qoe小于等于基于优先级
    的方法，从而表现上也更好一些。
  - 每次网络产生的总的qoe都在 *_group下的network.log里面。
  
        
  
