class Solution(object):


    def select_block(self, cur_time, block_queue):
        '''
        The alogrithm to select the block which will be sended in next.
        The following example is selecting block by the radio of rest life time to deadline.
        :param cur_time: float
        :param block_queue: the list of Block.You can get more detail about Block in objects/blocks.py
        :return: int
        '''
        def is_better(block):
            return (cur_time - block.timestamp) * best_block.deadline > \
                    (cur_time - best_block.timestamp) * block.deadline

        best_block_idx = -1
        best_block = None
        for idx, item in enumerate(block_queue):
            if best_block is None or is_better(item) :
                best_block_idx = idx
                best_block = item

        return best_block_idx
