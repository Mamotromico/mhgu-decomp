extern "C" {

void func_6056dc88(void *);
void func_6054533c(void *, int, int);

void func_6062f358(void *a)
{
    func_6056dc88(a);
    void *p = *(void **)((char *)a + 0x24);
    func_6054533c(p, 0x21, 0);
}

}