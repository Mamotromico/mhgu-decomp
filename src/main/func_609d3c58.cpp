extern "C" struct Input { int a; int b; int c; };

struct Output {
    char pad0[0xd30];
    int f_d30;
    int f_d34;
    int f_d38;
    int f_d3c;
    char pad1[0xd57 - 0xd40];
    unsigned char f_d57;
};

extern "C" void func_609d3c58(Output *o, const Input *i) {
    o->f_d30 = i->a;
    o->f_d34 = i->b;
    o->f_d38 = i->c;
    o->f_d3c = 0;
    o->f_d57 = 1;
}