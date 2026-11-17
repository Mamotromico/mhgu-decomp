extern "C" char D_6176765c[];

struct Obj {
    void *p0;      // +0x0
    unsigned short h4; // +0x4
    unsigned char pad6[2];
    int w8;        // +0x8
    int wc;        // +0xc
};

extern "C" void func_604b2418(Obj *o)
{
    o->p0 = &D_6176765c[8];
    o->h4 = 0;
    o->w8 = 0;
    o->wc = 0;
}