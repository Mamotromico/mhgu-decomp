extern "C" {

struct VTable;

struct B {
    VTable *vt;
};

struct VTable {
    char pad[8];
    int (*fn)(B *, unsigned short);
};

struct A {
    char pad[4];
    unsigned short val;
};

int func_602505f4(A *a, B *b) {
    return b->vt->fn(b, a->val);
}

}