

typedef struct {
    Node* prev;
    void* value;
} Node;

typedef LinkedList Node*;

LinkedList next(LinkedList n){
    if (n == nullptr)
        return nullptr;

    return n.prev;
}

void* get(LinkedList n){
    if (n == nullptr)
        return nullptr;

    return n.value;
}

// put the new element in front
LinkedList push_front(LinkedList list, void* data){
    LinkedList new_node = malloc(sizeof(Node) * 1)
    new_node.prev = list;
    new_node.value = data;
    return new_node;
}

// insert the element after the first element
LinkedList insert(LinkedList pos, void* data){
    LinkedList new_node = malloc(sizeof(Node) * 1)
    new_node.value = data;
    new_node.prev = pos.prev;
    pos.prev = new_node;
    return list;
}

// remove element that comes after pos
LinkedList remove_one(LinkedList pos, void* data){
    Node* node = pos.prev;
    pos.prev = node.prev;
    node.prev = nullptr;
    free_list(node);
}


void free_list(LinkedList pos){
    while (pos != nullptr){
        Node* node = pos;
        pos = pos.prev;
        free(node);
    }
}

