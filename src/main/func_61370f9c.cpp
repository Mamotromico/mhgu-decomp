struct Node {
    Node* prev;
    Node* next;
};

extern "C" void func_61370f9c(Node* pos, Node* node) {
    Node* next = pos->next;
    pos->next = node;
    node->prev = pos;
    node->next = next;
    if (next)
        next->prev = node;
}