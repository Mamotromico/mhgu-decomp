extern "C" char D_617675d4[];

struct S {
    char *p;        /* +0x0 */
    unsigned short h; /* +0x4 */
    char pad6[2];   /* +0x6 */
    int z;          /* +0x8 */
    int z2;         /* +0xc */
};

extern "C" void func_604b1f14(S *s)
{
    s->p = &D_617675d4[8];
    s->h = 0;
    s->z = 0;
    s->z2 = 0;
}