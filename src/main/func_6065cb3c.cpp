typedef struct {
    char _pad[0x34];
    int *arr;
} func_6065cb3c_obj;

extern "C" int func_6065cb3c(func_6065cb3c_obj *self, int index) {
    return self->arr[index];
}