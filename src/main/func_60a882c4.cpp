extern "C" void func_60a59268(void *p);

struct S {
    char pad[0x46];
    unsigned char b46;
};

extern "C" void func_60a882c4(struct S *p)
{
    func_60a59268(p);
    p->b46 = 0x36;
}