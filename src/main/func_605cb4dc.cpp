extern "C" {

void func_605cb504(void *);
void func_605cb6a8(void *);

struct S {
    char pad0[0x18];
    unsigned char flag; // +0x18
};

void func_605cb4dc(S *p)
{
    if (p->flag == 0)
        return;
    func_605cb504(p);
    func_605cb6a8(p);
}

}