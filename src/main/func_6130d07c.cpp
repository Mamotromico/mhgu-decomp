struct Node {
    Node* next;
    Node* prev;
};

struct List {
    char pad0[0xc];
    unsigned int count;
};

extern "C" void func_6130d07c(List* list, Node* node, Node* newNode)
{
    newNode->next = node;
    newNode->prev = node->prev;
    node->prev->next = newNode;
    node->prev = newNode;
    list->count++;
}