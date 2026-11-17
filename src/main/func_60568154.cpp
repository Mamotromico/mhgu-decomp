extern "C" {
void func_6056e4d8(void);
void func_60568174(void *);

void func_60568154(char *p)
{
    func_6056e4d8();
    func_60568174(p);
    *(unsigned *)(p + 0xb8) = 0;
}
}