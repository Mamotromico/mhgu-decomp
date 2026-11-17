extern "C" {

void func_6056e4d8(void);
void func_6058f930(void *p);

void func_6058f910(void *p)
{
    func_6056e4d8();
    func_6058f930(p);
    *(unsigned *)((char *)p + 0x50) = 0;
}

}