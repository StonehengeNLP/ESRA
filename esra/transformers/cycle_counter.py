import copy

class CycleCounter:
    """
        cycle_counter class for ESRA validator module.

        To get the number of cycle in graph use .count_cycle(data).       
    """

    def __init__(self,threshold):
        # init the list of relation_types that this module going to check
        self.relation_types = ['PART-OF','EVALUATE-FOR','USED-FOR','FEATURE-OF','HYPONYM-OF','REFER-TO']
        self.threshold = threshold

    def set_threshold(self,threshold):
        """
            Threshold setter.

            params:

                threshold: new threshold value.

        """
        self.threshold = threshold


    def __get_adjancency_lists(self,data):
        """
            Retrieve adjancency_list of graph of all relation types.

            params:

                - data: data object.

            return:
                
                - adjancency_lists: adjancency_list of all relation types.
        """
        entities = data['entities']
        relations = data['relations']
    
        adjancency_lists = [[[] for i in range(len(entities))] for j in range(len(self.relation_types))]
    
        for (rt_index,rt) in enumerate(self.relation_types):
            for current_rt, s_index, e_index, _ in relations:
                if current_rt.upper() == rt:
                    adjancency_lists[rt_index][s_index].append(e_index)
        return adjancency_lists



    def __is_cyclic_util(self,node_idx,visited,recStack,adjancency_list):
        """
            check isCyclic recursively.

            params:

                - node_idx: index of focusing node.

                - visited: list of boolean that keep visit status
                  of each node.

                - recStack: list of boolean that keep recursive stack
                  status of each node.
                
                - adjancency_list: adjancency_list of focusing relation type.

            return:
                
                - adjancency_lists: adjancency_list of all relation_types.
        """
        visited[node_idx] = True
        recStack[node_idx]= True
        
        for neighbour_idx in adjancency_list[node_idx]:
            if visited[neighbour_idx] == False:
                if self.__is_cyclic_util(neighbour_idx,visited,recStack,adjancency_list) == True:
                    return True
            elif recStack[neighbour_idx] == True:
                return True
        recStack[node_idx] = False
        return False



    def __count_cycle(self,data):
        """
            Count the number of cycle in the graph including self-loop.
            Cycle in this context mean the cycles of directed graph 
            which have same relation type.

            params:

                - data: data object.
            
            return:

                - n_cycle: the number of cycle in the graph.

        """
        adjancency_lists = self.__get_adjancency_lists(data)
        n_cycle = 0

        for adjancency_list in adjancency_lists:
            visited = [False] * len(adjancency_list)
            recStack = [False] * len(adjancency_list)
            for node_idx in range(len(adjancency_list)):
                if visited[node_idx] == False:
                    if self.__is_cyclic_util(node_idx,visited,recStack,adjancency_list) == True:
                        n_cycle += 1
        return n_cycle
    
    def cyclic_validate(self,data):
        """
            Validate the graph using threshold value. The graph
            will valid if the number of loop less than or equal
            to the threshold value

            params:

                data: {entities:[entity_type,entity_name],
                       relations:[relation_type,from_idx,to_idx]}

            return:

                boolean: True -> valid, False -> Invalid

        """
        
        if (self.__count_cycle(data) > self.threshold):
            return True
        else:
            return False

    def drop_self_loops(self, data):
        """
            Drop self loops for every relation types
            because they are always wrong and 
            do not need further consensus
            
            params:
                data
            return:
                data without self loops
        """
        
        data = copy.deepcopy(data)
        data['relations'] = [relation for relation in data['relations'] if relation[1] != relation[2]]
        return data