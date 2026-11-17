extern "C" {

extern char D_617676e4[];

struct S {
    unsigned char pad0[0x8];
};

void func_604b291c(struct S *p) {
    *(void **)((char *)p + 0x0) = (void *)(&D_617676e4[0x8]);
    *(unsigned short *)((char *)p + 0x4) = 0;
    *(unsigned *)((char *)p + 0x8) = 0;
    *(unsigned *)((char *)p + 0xc) = 0;
}

}