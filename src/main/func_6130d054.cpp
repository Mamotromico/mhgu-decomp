struct Node {
    Node* next;   // +0x0
    Node* prev;   // +0x4
};

struct List {
    char pad0[0xc];
    int count;    // +0xc
};

extern "C" void func_6130d054(List* list, Node* node, Node* pos) {
    Node* nextNode = node->next;
    pos->next = nextNode;
    pos->prev = node;
    Node* oldNext = node->next;
    oldNext->prev = pos;
    node->next = pos;
    list->count = list->count + 1;
}