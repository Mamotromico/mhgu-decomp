typedef unsigned short u16;

struct Base;

typedef int (*FnPtr)(struct Base *self, int arg, u16 a, u16 c);

struct FnObj {
    char pad[0x6c8];
    FnPtr fn;
};

struct Base {
    struct FnObj *obj;          /* +0x0000 */
    char pad1[0x2506 - 0x4];    /* pad to +0x2506 */
    u16 a;                      /* +0x2506 */
    char pad2[0x250a - 0x2506 - 2]; /* pad to +0x250a */
    u16 c;                      /* +0x250a */
};

extern "C" int func_602aa498(struct Base *p, int arg)
{
    return p->obj->fn(p, arg, p->a, p->c);
}