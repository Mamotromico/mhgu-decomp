extern "C" char D_617403b4[];

struct Obj {
    unsigned char pad0[8];
};

struct Out {
    void *p;
    unsigned char b;
};

extern "C" void func_601bb6c4(Out *o) {
    o->p = (void *)(&D_617403b4[8]);
    o->b = 0;
}