# Эмулятор оболочки (вариант 7)

Эмулятор командной строки UNIX с окном на tkinter.

## Этап 1

- в заголовке окна имя VFS
- парсер понимает аргументы в кавычках
- `ls`, `cd` - заглушки, выводят имя и аргументы
- `exit` - выход

## Запуск

```
run.bat
```

## Тесты

```
python -m unittest discover -s tests -t .
```

## Пример

```
vfs:~$ ls -l "my dir"
ls ['-l', 'my dir']
vfs:~$ cd a b
cd: too many arguments
vfs:~$ exit abc
exit: abc: numeric argument required
vfs:~$ hello
hello: command not found
vfs:~$ exit
```
