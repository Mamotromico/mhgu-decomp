extern "C" {

struct Inner {
    char pad0[0x8];
    unsigned int key;   // +0x8
};

struct Outer {
    Inner* arr;         // +0x0
    unsigned int count; // +0x4
    unsigned int minVal;// +0x8
};

struct Root {
    char pad[0x38];
    Outer* ptr;         // +0x38
};

unsigned int func_6122a198(Root* root, unsigned int val) {
    Outer* o = root->ptr;
    if (o == 0) return 0;
    if (o->minVal < val) return 0;
    unsigned int count = o->count;
    if (count == 0) return 0;
    Inner* p = o->arr;
    for (unsigned int i = 0; i < count; i++) {
        unsigned int k = p->key;
        if (k >= val) return k;
        p = (Inner*)((char*)p + 0x34);
    }
    return 0;
}

}