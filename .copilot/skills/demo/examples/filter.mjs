export function filterTasks(tasks, status) {
  if (!['all', 'open', 'done'].includes(status)) throw new Error('Unknown task filter');
  return tasks.filter((task) => status === 'all' || task.completed === (status === 'done'));
}
