struct Node {
    unsigned char pad[0x34];
    Node* next;
};

struct Holder {
    unsigned int field_0;
    Node* field_4;
};

extern "C" int func_607bba24(Holder* h) {
    Node* n = h->field_4;
    int count = 0;

    while (n != 0) {
        n = n->next;
        count++;
    }

    return count;
}