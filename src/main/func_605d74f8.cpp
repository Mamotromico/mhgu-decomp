extern "C" void func_6056df00(void *);

struct S {
    char pad[0x4c];
    unsigned char f4c;
    char pad2[0x3];
    unsigned f50;
};

extern "C" void func_605d74f8(S *p) {
    func_6056df00(p);
    p->f4c = 1;
    p->f50 = 0;
}