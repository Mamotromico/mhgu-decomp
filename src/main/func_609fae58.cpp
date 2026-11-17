extern "C" {

int func_609fa3d8(void *p);
int func_607c8a6c(void *p, int x);

struct S {
    char pad[0xb0];
};

int func_609fae58(struct S *s)
{
    int a = func_609fa3d8(s);
    int r = func_607c8a6c((char *)s + 0xb0, a);
    return r != 0;
}

}