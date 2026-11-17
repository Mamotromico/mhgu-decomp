extern "C" void func_6056dc28(void *);

struct Obj {
    char pad[0x88];
    unsigned char flag;
};

extern "C" void func_605dc8dc(struct Obj *p)
{
    func_6056dc28(p);
    p->flag = 0;
}