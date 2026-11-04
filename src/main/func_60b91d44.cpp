extern "C" void func_60b91d44(void* p);

struct Node {
    char pad0[0xc];
    unsigned int field_c;
};

struct Outer {
    Node* ptr[8];
};

extern "C" void func_60b91d44(void* p) {
    Outer* o = (Outer*)p;
    for (int i = 0; i < 8; i++) {
        Node* n = o->ptr[i];
        if (n == 0) continue;
        unsigned int v = (n->field_c & 0x7) - 1;
        if (v >= 2) {
            o->ptr[i] = 0;
        }
    }
}