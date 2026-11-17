extern char D_617677f4[];
struct S { char pad0[0x10]; };
extern "C" void func_604b3324(S *p)
{
    *(char **)p = &D_617677f4[0x8];
    *(unsigned short *)((char *)p + 0x4) = 0;
    *(unsigned *)((char *)p + 0x8) = 0;
    *(unsigned *)((char *)p + 0xc) = 0;
}