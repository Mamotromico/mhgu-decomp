struct Node {
    char pad[0x14];
    Node* next;
};

struct Root {
    char pad[0x648];
    Node* head;
};

extern "C" Node* func_602306cc(Root* root) {
    Node* v1 = root->head;
    Node* v2;

    do {
        v2 = v1;
        v1 = v2->next;
    } while (v1 != 0);

    return v2;
}