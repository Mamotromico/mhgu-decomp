struct Node {
    char pad0[0x70];
    struct Node *next;
    int field1;
    char pad1[4];
    int field2;
};

extern "C" struct Node *func_60578d14(struct Node *n, int v) {
    n->field1 = v;
    struct Node *p = n->next;
    p->field2 = v;
    return p;
}