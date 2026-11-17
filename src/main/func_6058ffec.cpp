extern "C" {
void func_6056e4d8(void *p);
void func_6059000c(void *p);
}

extern "C" void func_6058ffec(void *p)
{
    func_6056e4d8(p);
    func_6059000c(p);
    *(unsigned *)((char *)p + 0x50) = 0;
}