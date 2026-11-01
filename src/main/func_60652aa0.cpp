extern "C" struct In {
    char pad0[0];
    short a;      // +0x0
    short b;      // +0x2
    unsigned int c; // +0x4
    unsigned int d; // +0x8
};

struct Out {
    char pad0[0x88];
    unsigned int f88;  // +0x88
    unsigned int f8c;  // +0x8c
    int f90;           // +0x90
    int f94;           // +0x94
};

extern "C" void func_60652aa0(Out* o, In* i) {
    o->f90 = i->a;
    o->f94 = i->b;
    o->f88 = i->c;
    o->f8c = i->d;
}