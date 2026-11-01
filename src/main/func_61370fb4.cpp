struct Node {
    Node *next;
    Node *prev;
};

extern "C" void func_61370fb4(Node *a, Node *b) {
    Node *tmp = a->next;
    a->next = b;
    b->next = tmp;
    b->prev = a;
    if (tmp)
        tmp->prev = b;
}