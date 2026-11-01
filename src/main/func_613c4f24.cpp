struct Node {
    char pad[0x1c];
    Node* next;
};

extern "C" unsigned int func_613c4f24(Node* node) {
    unsigned int count = 0;
    while (node != 0) {
        node = node->next;
        ++count;
    }
    return count;
}