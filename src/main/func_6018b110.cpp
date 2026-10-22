typedef unsigned short u16;

typedef int (*Handler)(void *, u16, u16, u16 *);

extern "C" int func_6018b110(void *ctx, int index)
{
    u16 *p = (u16 *)ctx;
    void *v = *(void **)p;
    p += index;
    Handler h = *(Handler *)((char *)v + 0x1c);
    return h(ctx, p[6], p[4], p);
}