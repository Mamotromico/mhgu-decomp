extern char D_61834808[];

struct S {
    void *p;      /* +0x0 */
    unsigned short h; /* +0x4 */
    unsigned char b;  /* +0x6 */
};

extern "C" void func_6135a7d8(struct S *s)
{
    s->p = &D_61834808[8];
    s->h = 0;
    s->b = 0;
}